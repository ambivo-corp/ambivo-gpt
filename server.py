#!/usr/bin/env python3
"""
GPT Actions Server - Standalone HTTP server for ChatGPT integration
Provides OpenAPI-compatible endpoints without Tornado dependency
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime, UTC
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from urllib.parse import urlparse, parse_qs
import threading

# Version timestamp - automatically updated on git push
VERSION_TIMESTAMP = "2025-08-01T21:38:48Z"

# Import local MCP core functionality
from mcp_core import handle_list_tools, handle_call_tool, api_client


class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    """Thread-per-request HTTP server"""
    daemon_threads = True


class GPTActionsHandler(BaseHTTPRequestHandler):
    """HTTP request handler for GPT Actions"""
    
    def log_message(self, format, *args):
        """Override to use logging instead of stderr"""
        logging.info(f"{self.address_string()} - {format % args}")
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
    
    def do_GET(self):
        """Handle GET requests"""
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        
        if path == '/':
            self._handle_root()
        elif path == '/.well-known/ai-plugin.json':
            self._handle_ai_plugin()
        elif path == '/openapi.yaml':
            self._handle_openapi_spec()
        elif path == '/openapi.json':
            self._handle_openapi_spec(format='json')
        elif path == '/openapi-test.json':
            self._handle_test_openapi()
        elif path == '/schema.json':
            self._handle_openapi_spec(format='json')
        elif path == '/debug':
            self._handle_debug()
        elif path == '/api-spec':
            self._handle_openapi_spec(format='json')
        elif path == '/health':
            self._handle_health()
        elif path == '/tools':
            self._handle_list_tools()
        else:
            self._send_error(404, "Not Found")
    
    def do_POST(self):
        """Handle POST requests"""
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        
        if path == '/tools':
            self._handle_call_tool()
        elif path == '/query':
            self._handle_natural_query()
        else:
            self._send_error(404, "Not Found")
    
    def _get_auth_token(self):
        """Extract auth token from Authorization header"""
        auth_header = self.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            return auth_header[7:]
        return None
    
    def _send_json_response(self, data, status_code=200):
        """Send JSON response"""
        response_data = json.dumps(data, indent=2).encode('utf-8')
        
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(response_data)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(response_data)
    
    def _send_error(self, status_code, message):
        """Send error response"""
        self._send_json_response({"error": message}, status_code)
    
    def _handle_root(self):
        """Handle root endpoint - API documentation"""
        docs = {
            "name": "Ambivo GPT Actions API",
            "version": "1.0.0",
            "description": "Direct API for ChatGPT integration with Ambivo CRM data",
            "endpoints": {
                "GET /": "API documentation",
                "GET /.well-known/ai-plugin.json": "AI plugin manifest",
                "GET /openapi.yaml": "OpenAPI specification",
                "GET /health": "Health check",
                "GET /tools": "List available tools",
                "POST /tools": "Call a specific tool",
                "POST /query": "Natural language query"
            },
            "authentication": {
                "type": "Bearer Token",
                "description": "Include JWT token in Authorization header"
            }
        }
        self._send_json_response(docs)
    
    def _handle_ai_plugin(self):
        """Handle AI plugin manifest for ChatGPT"""
        manifest = {
            "schema_version": "v1",
            "name_for_human": "Ambivo CRM",
            "name_for_model": "ambivo_crm",
            "description_for_human": "Access and query Ambivo CRM data using natural language",
            "description_for_model": "Plugin for querying Ambivo CRM data including leads, contacts, deals, and other entities using natural language queries or direct API calls.",
            "auth": {
                "type": "bearer"
            },
            "api": {
                "type": "openapi",
                "url": f"http://{self.headers.get('Host', 'localhost')}/openapi.yaml"
            },
            "logo_url": "https://ambivo.com/logo.png",
            "contact_email": "dev@ambivo.com",
            "legal_info_url": "https://ambivo.com/legal"
        }
        self._send_json_response(manifest)
    
    def _handle_openapi_spec(self, format='yaml'):
        """Handle OpenAPI specification"""
        from schema_generator import generate_openapi_schema
        
        try:
            # Generate OpenAPI schema from MCP tools
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                schema = loop.run_until_complete(generate_openapi_schema())
            finally:
                loop.close()
            
            # Update servers section with actual host
            host = self.headers.get('Host', 'localhost:8080')
            # Use HTTPS for production domains
            protocol = 'https' if ('railway.app' in host or 'herokuapp.com' in host or 
                                  'ambivo.com' in host or 'onrender.com' in host or 
                                  'vercel.app' in host or host != 'localhost:8080') else 'http'
            
            # Create a new ordered schema to ensure proper structure for ChatGPT
            ordered_schema = {
                "openapi": schema.get("openapi", "3.1.0"),
                "info": schema.get("info", {}),
                "servers": [
                    {
                        "url": f"{protocol}://{host}",
                        "description": "Production server"
                    }
                ],
                "paths": schema.get("paths", {}),
                "components": schema.get("components", {}),
                "security": schema.get("security", [])
            }
            
            # Use the ordered schema
            schema = ordered_schema
            
            # Send response based on format
            if format == 'json':
                self._send_json_response(schema)
            else:
                # Send as YAML
                import yaml
                yaml_content = yaml.dump(schema, default_flow_style=False, sort_keys=False).encode('utf-8')
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/x-yaml')
                self.send_header('Content-Length', str(len(yaml_content)))
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(yaml_content)
            
        except Exception as e:
            logging.error(f"Error generating OpenAPI spec: {e}")
            self._send_error(500, f"Error generating OpenAPI spec: {str(e)}")
    
    def _handle_test_openapi(self):
        """Return a test OpenAPI spec that matches exactly what ChatGPT expects"""
        # Try the exact format from OpenAI's examples
        test_spec = {
            "openapi": "3.1.0",
            "info": {
                "title": "Ambivo CRM API",
                "description": "Access Ambivo CRM data",
                "version": "1.0.0"
            },
            "servers": [
                {
                    "url": "https://gpt.ambivo.com"
                }
            ],
            "paths": {
                "/query": {
                    "post": {
                        "operationId": "queryData",
                        "summary": "Query CRM data",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "query": {
                                                "type": "string"
                                            }
                                        }
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Successful response",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object"
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        
        self._send_json_response(test_spec)
    
    def _handle_debug(self):
        """Debug endpoint to check what's happening"""
        self._send_json_response({
            "message": "Debug endpoint working",
            "version": VERSION_TIMESTAMP,
            "paths": {
                "health": "/health - working",
                "openapi_json": "/openapi.json - 501 error", 
                "schema_json": "/schema.json - alternative",
                "query": "/query - working"
            },
            "timestamp": datetime.now(UTC).isoformat()
        })
    
    def _handle_health(self):
        """Handle health check"""
        try:
            # Test MCP tool availability
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                tools = loop.run_until_complete(handle_list_tools())
                tool_names = [tool.name for tool in tools]
            finally:
                loop.close()
            
            self._send_json_response({
                "status": "healthy",
                "timestamp": datetime.now(UTC).isoformat(),
                "available_tools": tool_names,
                "server_type": "gpt_actions",
                "version": VERSION_TIMESTAMP,
                "deployment_info": {
                    "version_timestamp": VERSION_TIMESTAMP,
                    "build_time": datetime.now(UTC).isoformat()
                }
            })
            
        except Exception as e:
            logging.error(f"Health check error: {e}")
            self._send_error(500, f"Health check failed: {str(e)}")
    
    def _handle_list_tools(self):
        """Handle GET /tools - List available tools"""
        try:
            auth_token = self._get_auth_token()
            if not auth_token:
                self._send_error(401, "Authorization token required")
                return
            
            # Token validation happens at the API level
            
            # Get tools from MCP server
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                mcp_tools = loop.run_until_complete(handle_list_tools())
            finally:
                loop.close()
            
            # Convert to OpenAI function calling format
            tools = []
            for tool in mcp_tools:
                tool_def = {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema
                }
                tools.append(tool_def)
            
            self._send_json_response({
                "tools": tools,
                "server_info": {
                    "name": "ambivo-gpt-actions",
                    "version": "1.0.0",
                    "capabilities": ["natural_language_queries", "crm_data_access"]
                }
            })
            
        except Exception as e:
            logging.error(f"List tools error: {e}")
            self._send_error(500, str(e))
    
    def _handle_call_tool(self):
        """Handle POST /tools - Call a specific tool"""
        try:
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            auth_token = self._get_auth_token()
            if not auth_token:
                self._send_error(401, "Authorization token required")
                return
            
            tool_name = data.get('name') or data.get('function_name')
            arguments = data.get('arguments', {})
            
            if not tool_name:
                self._send_error(400, "Tool name is required")
                return
            
            # Set the auth token from the request header for this request
            original_token = api_client.auth_token
            api_client.set_auth_token(auth_token)
            
            # Call the MCP tool
            try:
                # Check if there's already an event loop running
                try:
                    loop = asyncio.get_running_loop()
                    # Use run_coroutine_threadsafe for existing loop
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(
                            asyncio.run,
                            handle_call_tool(tool_name, arguments)
                        )
                        result = future.result(timeout=30)
                except RuntimeError:
                    # No event loop running, create new one
                    result = asyncio.run(handle_call_tool(tool_name, arguments))
            finally:
                # Restore original token (if any)
                if original_token:
                    api_client.auth_token = original_token
                else:
                    api_client.auth_token = None
            
            # Format response
            response_text = ""
            for content in result:
                response_text += content.text + "\n"
            
            self._send_json_response({
                "result": response_text.strip(),
                "tool_name": tool_name,
                "success": True
            })
            
        except Exception as e:
            logging.error(f"Call tool error: {e}")
            self._send_error(500, str(e))
    
    def _handle_natural_query(self):
        """Handle POST /query - Natural language query"""
        try:
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            auth_token = self._get_auth_token()
            if not auth_token:
                self._send_error(401, "Authorization token required")
                return
            
            query = data.get('query')
            response_format = data.get('response_format', 'both')
            
            if not query:
                self._send_error(400, "Query parameter is required")
                return
            
            # Set the auth token from the request header for this request
            original_token = api_client.auth_token
            api_client.set_auth_token(auth_token)
            
            # Call the natural query tool
            try:
                # Check if there's already an event loop running
                try:
                    loop = asyncio.get_running_loop()
                    # Use run_coroutine_threadsafe for existing loop
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(
                            asyncio.run,
                            handle_call_tool('natural_query', {
                                'query': query,
                                'response_format': response_format
                            })
                        )
                        result = future.result(timeout=30)
                except RuntimeError:
                    # No event loop running, create new one
                    result = asyncio.run(handle_call_tool('natural_query', {
                        'query': query,
                        'response_format': response_format
                    }))
            finally:
                # Restore original token (if any)
                if original_token:
                    api_client.auth_token = original_token
                else:
                    api_client.auth_token = None
            
            # Format response
            response_text = ""
            for content in result:
                response_text += content.text + "\n"
            
            self._send_json_response({
                "query": query,
                "result": response_text.strip(),
                "response_format": response_format,
                "timestamp": datetime.now(UTC).isoformat(),
                "success": True
            })
            
        except Exception as e:
            logging.error(f"Natural query error: {e}")
            self._send_error(500, str(e))


class GPTActionsServer:
    """GPT Actions HTTP Server"""
    
    def __init__(self, host='localhost', port=8080):
        self.host = host
        self.port = port
        self.server = None
        self.server_thread = None
    
    def start(self, blocking=True):
        """Start the server"""
        logging.info(f"Starting GPT Actions server on {self.host}:{self.port}")
        
        self.server = ThreadingHTTPServer((self.host, self.port), GPTActionsHandler)
        
        if blocking:
            try:
                self.server.serve_forever()
            except KeyboardInterrupt:
                logging.info("Server interrupted")
                self.stop()
        else:
            self.server_thread = threading.Thread(target=self.server.serve_forever)
            self.server_thread.daemon = True
            self.server_thread.start()
            logging.info(f"Server started in background thread")
    
    def stop(self):
        """Stop the server"""
        if self.server:
            logging.info("Stopping GPT Actions server")
            self.server.shutdown()
            self.server.server_close()
        
        if self.server_thread:
            self.server_thread.join(timeout=5)
    
    def get_base_url(self):
        """Get the base URL of the server"""
        return f"http://{self.host}:{self.port}"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    server = GPTActionsServer()
    server.start()