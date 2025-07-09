# 3. cursor_integration.py - Cursor IDE Integration
cat > ~/ai-config/cursor_integration.py << 'EOF'
#!/usr/bin/env python3
"""
Cursor IDE Integration
HTTP-Server für Cursor AI Provider Integration
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import threading
from smart_router import SmartAIRouter

class CursorAIHandler(BaseHTTPRequestHandler):
    
    def __init__(self, *args, **kwargs):
        self.router = SmartAIRouter()
        super().__init__(*args, **kwargs)
    
    def do_POST(self):
        """Handle Cursor AI requests"""
        if self.path == "/v1/chat/completions":
            self.handle_chat_completion()
        else:
            self.send_error(404, "Not Found")
    
    def handle_chat_completion(self):
        """OpenAI-compatible chat completion endpoint"""
        try:
            # Read request body
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)
            request_data = json.loads(body.decode('utf-8'))
            
            # Extract prompt from messages
            messages = request_data.get('messages', [])
            if not messages:
                raise ValueError("No messages provided")
            
            # Combine messages into single prompt
            prompt = "\n".join([msg.get('content', '') for msg in messages if msg.get('content')])
            
            # Route request
            result = self.router.route_request(prompt)
            
            if result["success"]:
                # Format as OpenAI-compatible response
                response_data = {
                    "id": "cursor-ai-router",
                    "object": "chat.completion",
                    "created": int(__import__('time').time()),
                    "model": result["model"],
                    "choices": [{
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": result["response"]
                        },
                        "finish_reason": "stop"
                    }],
                    "usage": {
                        "prompt_tokens": result["tokens"]["input"],
                        "completion_tokens": result["tokens"]["output"],
                        "total_tokens": result["tokens"]["input"] + result["tokens"]["output"]
                    },
                    "router_info": {
                        "cost": result["cost"],
                        "budget_remaining": result["budget_status"]["remaining"],
                        "routing_reason": result["routing_reason"]
                    }
                }
                
                # Send response
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(response_data).encode('utf-8'))
                
            else:
                self.send_error(500, f"AI Router Error: {result['error']}")
                
        except Exception as e:
            self.send_error(500, f"Server Error: {str(e)}")
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
    
    def log_message(self, format, *args):
        """Override to reduce log noise"""
        return

def start_server(port=8000):
    """Start HTTP server for Cursor integration"""
    server = HTTPServer(('localhost', port), CursorAIHandler)
    print(f"🚀 Cursor AI Router Server läuft auf http://localhost:{port}")
    print(f"📋 Cursor AI Provider URL: http://localhost:{port}/v1/chat/completions")
    print(f"🤖 Model Name: intelligent-router")
    print("🛑 Stoppen mit Ctrl+C")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n⏹️  Server gestoppt")
        server.shutdown()

if __name__ == "__main__":
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    start_server(port)
EOF
