#!/usr/bin/env python3
"""
Smart AI Router with $5 Budget Control
Intelligente Weiterleitung zwischen Ollama (kostenlos) und Claude API (bezahlt)
"""

import os
import json
import requests
import datetime
from typing import Dict, List, Optional
from anthropic import Anthropic
from pathlib import Path

class SmartAIRouter:
    def __init__(self, config_path: str = "~/ai-config/router_config.json"):
        self.config_path = Path(config_path).expanduser()
        self.config = self.load_config()
        self.budget_file = Path(config_path).parent / "budget_tracker.json"
        self.claude_client = None
        
        # Initialize Claude client if API key available
        if self.config.get("claude_api_key"):
            self.claude_client = Anthropic(api_key=self.config["claude_api_key"])
    
    def load_config(self) -> Dict:
        """Lädt Router-Konfiguration"""
        default_config = {
            "claude_api_key": "",
            "ollama_base_url": "http://localhost:11434",
            "monthly_budget": 5.0,
            "warning_threshold": 4.0,
            "escalation_keywords": [
                "architecture", "design", "system", "complex", "ASPICE", 
                "compliance", "review", "analysis", "strategy", "planning"
            ],
            "ollama_keywords": [
                "code", "refactor", "test", "debug", "simple", "function",
                "fix", "error", "variable", "loop", "class"
            ],
            "cost_per_input_token": 0.000003,  # Claude Sonnet
            "cost_per_output_token": 0.000015
        }
        
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                # Merge with defaults
                default_config.update(config)
        else:
            # Create config directory and file
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
                
        return default_config
    
    def save_config(self):
        """Speichert aktuelle Konfiguration"""
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def get_budget_status(self) -> Dict:
        """Überprüft aktuellen Budget-Status"""
        current_month = datetime.datetime.now().strftime("%Y-%m")
        
        if self.budget_file.exists():
            with open(self.budget_file, 'r') as f:
                budget_data = json.load(f)
        else:
            budget_data = {}
        
        if current_month not in budget_data:
            budget_data[current_month] = {"spent": 0.0, "requests": 0}
        
        return {
            "current_month": current_month,
            "spent": budget_data[current_month]["spent"],
            "requests": budget_data[current_month]["requests"],
            "budget": self.config["monthly_budget"],
            "remaining": self.config["monthly_budget"] - budget_data[current_month]["spent"],
            "budget_data": budget_data
        }
    
    def update_budget(self, cost: float):
        """Aktualisiert Budget-Tracking"""
        budget_status = self.get_budget_status()
        current_month = budget_status["current_month"]
        budget_data = budget_status["budget_data"]
        
        budget_data[current_month]["spent"] += cost
        budget_data[current_month]["requests"] += 1
        
        # Keep only last 3 months
        months_to_keep = sorted(budget_data.keys())[-3:]
        budget_data = {month: budget_data[month] for month in months_to_keep}
        
        with open(self.budget_file, 'w') as f:
            json.dump(budget_data, f, indent=2)
    
    def should_escalate_to_claude(self, prompt: str) -> tuple[bool, str]:
        """Entscheidet ob Claude API nötig ist"""
        budget_status = self.get_budget_status()
        
        # Budget-Check
        if budget_status["remaining"] <= 0:
            return False, "Budget erschöpft - Fallback zu Ollama"
        
        if budget_status["remaining"] < 0.5:  # Weniger als 50 Cent übrig
            return False, "Budget niedrig - Ollama bevorzugt"
        
        # Keyword-basierte Entscheidung
        prompt_lower = prompt.lower()
        
        # Force Ollama für einfache Tasks
        if any(keyword in prompt_lower for keyword in self.config["ollama_keywords"]):
            return False, "Einfache Coding-Task - Ollama ausreichend"
        
        # Escalate zu Claude für komplexe Tasks
        if any(keyword in prompt_lower for keyword in self.config["escalation_keywords"]):
            return True, "Komplexe Task - Claude erforderlich"
        
        # Längen-basierte Entscheidung
        if len(prompt) > 1000:  # Lange, komplexe Prompts
            return True, "Langer Prompt - Claude für bessere Qualität"
        
        # Default: Ollama (kostenlos)
        return False, "Standard-Task - Ollama Standard"
    
    def call_ollama(self, prompt: str, model: str = "mistral") -> Dict:
        """Ruft Ollama API auf"""
        try:
            response = requests.post(
                f"{self.config['ollama_base_url']}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9
                    }
                },
                timeout=120
            )
            response.raise_for_status()
            
            result = response.json()
            return {
                "success": True,
                "response": result["response"],
                "model": f"ollama-{model}",
                "cost": 0.0,
                "tokens": {"input": 0, "output": 0}  # Ollama doesn't provide token counts
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "fallback": True
            }
    
    def call_claude(self, prompt: str) -> Dict:
        """Ruft Claude API auf"""
        if not self.claude_client:
            return {
                "success": False,
                "error": "Claude API key nicht konfiguriert",
                "fallback": True
            }
        
        try:
            response = self.claude_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Grobe Token-Schätzung (Claude zählt nicht genau)
            input_tokens = len(prompt) // 4  # Approximation
            output_tokens = len(response.content[0].text) // 4
            
            cost = (input_tokens * self.config["cost_per_input_token"] + 
                   output_tokens * self.config["cost_per_output_token"])
            
            # Budget aktualisieren
            self.update_budget(cost)
            
            return {
                "success": True,
                "response": response.content[0].text,
                "model": "claude-3-sonnet",
                "cost": cost,
                "tokens": {"input": input_tokens, "output": output_tokens}
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "fallback": True
            }
    
    def route_request(self, prompt: str, force_model: Optional[str] = None) -> Dict:
        """Haupt-Routing-Funktion"""
        
        if force_model == "ollama":
            should_use_claude = False
            reason = "Erzwungen: Ollama"
        elif force_model == "claude":
            should_use_claude = True
            reason = "Erzwungen: Claude"
        else:
            should_use_claude, reason = self.should_escalate_to_claude(prompt)
        
        print(f"🤖 Routing-Entscheidung: {'Claude API' if should_use_claude else 'Ollama'}")
        print(f"📝 Grund: {reason}")
        
        if should_use_claude:
            result = self.call_claude(prompt)
            if not result["success"] and result.get("fallback"):
                print("⚠️  Claude fehlgeschlagen - Fallback zu Ollama")
                result = self.call_ollama(prompt)
        else:
            result = self.call_ollama(prompt)
            if not result["success"] and result.get("fallback"):
                print("⚠️  Ollama fehlgeschlagen - Kein Fallback verfügbar")
        
        # Budget-Status hinzufügen
        result["budget_status"] = self.get_budget_status()
        result["routing_reason"] = reason
        
        return result

# Convenience functions for file-based integration
def create_router_instance():
    """Erstellt Router-Instanz"""
    return SmartAIRouter()

def route_prompt(prompt: str, force_model: Optional[str] = None) -> str:
    """Einfache Funktion für File-basierte Integration"""
    router = create_router_instance()
    result = router.route_request(prompt, force_model)
    
    if result["success"]:
        return result["response"]
    else:
        return f"Fehler: {result.get('error', 'Unbekannter Fehler')}"

def setup_config(claude_api_key: str):
    """Initial Setup - API Key konfigurieren"""
    router = SmartAIRouter()
    router.config["claude_api_key"] = claude_api_key
    router.save_config()
    print("✅ Konfiguration gespeichert!")
    
    # Test both endpoints
    print("\n🧪 Teste Ollama-Verbindung...")
    ollama_result = router.call_ollama("Hello, test message")
    if ollama_result["success"]:
        print("✅ Ollama funktioniert!")
    else:
        print(f"❌ Ollama Fehler: {ollama_result['error']}")
    
    print("\n🧪 Teste Claude API...")
    claude_result = router.call_claude("Hello, test message")
    if claude_result["success"]:
        print("✅ Claude API funktioniert!")
        print(f"💰 Test-Kosten: ${claude_result['cost']:.4f}")
    else:
        print(f"❌ Claude API Fehler: {claude_result['error']}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python smart_router.py setup <claude_api_key>")
        print("  python smart_router.py prompt '<your prompt>'")
        print("  python smart_router.py budget")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "setup":
        if len(sys.argv) < 3:
            print("Error: API Key erforderlich")
            sys.exit(1)
        setup_config(sys.argv[2])
    
    elif command == "prompt":
        if len(sys.argv) < 3:
            print("Error: Prompt erforderlich")
            sys.exit(1)
        
        prompt = sys.argv[2]
        force_model = sys.argv[3] if len(sys.argv) > 3 else None
        
        router = SmartAIRouter()
        result = router.route_request(prompt, force_model)
        
        if result["success"]:
            print(f"\n🤖 Antwort ({result['model']}):")
            print(result["response"])
            if result["cost"] > 0:
                print(f"\n💰 Kosten: ${result['cost']:.4f}")
                print(f"📊 Budget übrig: ${result['budget_status']['remaining']:.2f}")
        else:
            print(f"❌ Fehler: {result['error']}")
    
    elif command == "budget":
        router = SmartAIRouter()
        status = router.get_budget_status()
        print(f"\n📊 Budget-Status ({status['current_month']}):")
        print(f"💰 Ausgegeben: ${status['spent']:.2f} / ${status['budget']:.2f}")
        print(f"📈 Verbleibendes Budget: ${status['remaining']:.2f}")
        print(f"🔢 API-Aufrufe: {status['requests']}")
        
        if status['remaining'] < 1.0:
            print("⚠️  Budget niedrig!")
    
    else:
        print(f"Unbekannter Befehl: {command}")
        sys.exit(1)
