# 2. file_router.py - File-basierte Integration
cat > ~/ai-config/file_router.py << 'EOF'
#!/usr/bin/env python3
"""
File-basierte AI-Router Integration
Für Ihr geplantes file-basiertes Workflow-System
"""

import os
import json
import sys
from pathlib import Path
from smart_router import SmartAIRouter

class FileBasedWorkflow:
    def __init__(self, workspace_dir: str = "~/projects"):
        self.workspace = Path(workspace_dir).expanduser()
        self.router = SmartAIRouter()
        
        # Ensure directories exist
        for subdir in ["features", "architecture", "documentation", "context"]:
            (self.workspace / subdir).mkdir(parents=True, exist_ok=True)
    
    def process_file_request(self, input_file: str, output_file: str, task_type: str = "auto"):
        """
        Verarbeitet File-basierte AI-Requests
        
        Args:
            input_file: Pfad zur Input-Datei
            output_file: Pfad zur Output-Datei  
            task_type: "code", "architecture", "review", "auto"
        """
        input_path = Path(input_file)
        output_path = Path(output_file)
        
        if not input_path.exists():
            print(f"❌ Input-Datei nicht gefunden: {input_file}")
            return False
        
        # Read input
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Determine task type from filename or content if auto
        if task_type == "auto":
            if "architecture" in str(input_path) or "design" in str(input_path):
                task_type = "architecture"
            elif "review" in str(input_path):
                task_type = "review"
            else:
                task_type = "code"
        
        # Create AI prompt based on task type
        prompt = self.create_prompt(content, task_type, input_path)
        
        # Force model based on task type
        force_model = "claude" if task_type in ["architecture", "review"] else None
        
        print(f"🔄 Verarbeite {input_path.name} -> {output_path.name}")
        print(f"📋 Task-Type: {task_type}")
        
        # Route request
        result = self.router.route_request(prompt, force_model)
        
        if result["success"]:
            # Write output
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(self.format_output(result, task_type, input_path))
            
            print(f"✅ Output geschrieben: {output_path}")
            if result["cost"] > 0:
                print(f"💰 Kosten: ${result['cost']:.4f}")
            
            return True
        else:
            print(f"❌ Fehler: {result['error']}")
            return False
    
    def create_prompt(self, content: str, task_type: str, input_path: Path) -> str:
        """Erstellt task-spezifische Prompts"""
        
        base_context = f"""
File: {input_path.name}
Task: {task_type}
Project Context: Healthcare VRP System (ASPICE-konform)

Input Content:
{content}

"""
        
        if task_type == "code":
            return base_context + """
Bitte analysiere und verbessere den Code:
1. Code-Qualität und Best-Practices
2. Performance-Optimierungen
3. Fehlerbehandlung
4. Dokumentation
5. ASPICE-Traceability-Kommentare

Gib den verbesserten Code mit Erklärungen zurück.
"""
        
        elif task_type == "architecture":
            return base_context + """
Erstelle eine detaillierte Architektur-Analyse:
1. System-Design-Entscheidungen
2. ASPICE-Compliance-Bewertung
3. Healthcare-Domain-Spezifika
4. Performance- und Skalierbarkeits-Überlegungen
5. Sicherheits- und DSGVO-Aspekte
6. Verbesserungsvorschläge

Format: Strukturiertes Markdown-Dokument
"""
        
        elif task_type == "review":
            return base_context + """
Führe ein umfassendes Code/Design-Review durch:
1. ASPICE-Requirements-Traceability
2. Healthcare-Compliance (DSGVO, gematik)
3. Code-Qualität und Architektur
4. Test-Coverage und Qualitätssicherung
5. Dokumentations-Vollständigkeit
6. Konkrete Verbesserungsvorschläge

Priorisiere Findings nach Kritikalität.
"""
        
        else:  # generic
            return base_context + """
Analysiere den Inhalt und gib relevante Verbesserungsvorschläge:
"""
    
    def format_output(self, result: dict, task_type: str, input_path: Path) -> str:
        """Formatiert AI-Output für File-System"""
        
        timestamp = __import__('datetime').datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        header = f"""# AI-Analyse: {input_path.name}

**Generiert:** {timestamp}
**Model:** {result['model']}
**Task-Type:** {task_type}
**Routing-Grund:** {result['routing_reason']}
"""
        
        if result['cost'] > 0:
            header += f"**Kosten:** ${result['cost']:.4f}\n"
        
        header += f"**Budget verbleibend:** ${result['budget_status']['remaining']:.2f}\n"
        header += "\n---\n\n"
        
        return header + result['response']

def main():
    if len(sys.argv) < 4:
        print("Usage: python file_router.py <input_file> <output_file> [task_type]")
        print("Task types: code, architecture, review, auto")
        print("")
        print("Examples:")
        print("  python file_router.py features/vrp_core.py features/vrp_analysis.md code")
        print("  python file_router.py architecture/system_design.md architecture/review.md architecture")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    task_type = sys.argv[3] if len(sys.argv) > 3 else "auto"
    
    workflow = FileBasedWorkflow()
    success = workflow.process_file_request(input_file, output_file, task_type)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
EOF
