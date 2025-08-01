#!/usr/bin/env python3
"""
OpenAPI Schema Generator
Generates OpenAPI 3.0 specification from MCP tools for ChatGPT integration
"""

import sys
import os
from typing import Dict, Any

# Import local MCP core functionality
from mcp_core import handle_list_tools


async def generate_openapi_schema() -> Dict[str, Any]:
    """Generate OpenAPI 3.0 schema from MCP tools"""
    
    # Get available tools from MCP server
    tools = await handle_list_tools()
    
    # Base OpenAPI structure
    schema = {
        "openapi": "3.1.0",
        "info": {
            "title": "Ambivo CRM API",
            "description": "API for accessing and querying Ambivo CRM data using natural language and direct tool calls",
            "version": "1.0.0",
            "contact": {
                "name": "Ambivo Support",
                "email": "dev@ambivo.com",
                "url": "https://ambivo.com"
            },
            "license": {
                "name": "MIT",
                "url": "https://opensource.org/licenses/MIT"
            }
        },
        "servers": [
            {
                "url": "http://localhost:8080",
                "description": "Local development server"
            }
        ],
        "security": [
            {
                "bearerAuth": []
            }
        ],
        "components": {
            "securitySchemes": {
                "bearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                    "description": "JWT token for API authentication"
                }
            },
            "schemas": {
                "Error": {
                    "type": "object",
                    "properties": {
                        "error": {
                            "type": "string",
                            "description": "Error message"
                        }
                    },
                    "required": ["error"]
                },
                "ToolResponse": {
                    "type": "object",
                    "properties": {
                        "result": {
                            "type": "string",
                            "description": "Tool execution result"
                        },
                        "tool_name": {
                            "type": "string",
                            "description": "Name of the executed tool"
                        },
                        "success": {
                            "type": "boolean",
                            "description": "Whether the tool executed successfully"
                        }
                    },
                    "required": ["result", "tool_name", "success"]
                },
                "QueryResponse": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Original query"
                        },
                        "result": {
                            "type": "string",
                            "description": "Query result"
                        },
                        "response_format": {
                            "type": "string",
                            "description": "Format of the response"
                        },
                        "timestamp": {
                            "type": "string",
                            "format": "date-time",
                            "description": "Query timestamp"
                        },
                        "success": {
                            "type": "boolean",
                            "description": "Whether the query succeeded"
                        }
                    },
                    "required": ["query", "result", "success"]
                }
            }
        },
        "paths": {}
    }
    
    # Add health check endpoint
    schema["paths"]["/health"] = {
        "get": {
            "summary": "Health Check",
            "description": "Check API health and list available tools",
            "operationId": "health_check",
            "responses": {
                "200": {
                    "description": "API is healthy",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "status": {"type": "string"},
                                    "timestamp": {"type": "string", "format": "date-time"},
                                    "available_tools": {
                                        "type": "array",
                                        "items": {"type": "string"}
                                    },
                                    "server_type": {"type": "string"}
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    
    # Add natural language query endpoint
    schema["paths"]["/query"] = {
        "post": {
            "summary": "Natural Language Query",
            "description": "Query Ambivo CRM data using natural language",
            "operationId": "natural_language_query",
            "security": [{"bearerAuth": []}],
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "Natural language query about CRM data",
                                    "example": "Show me leads created this week"
                                },
                                "response_format": {
                                    "type": "string",
                                    "enum": ["table", "natural", "both"],
                                    "default": "both",
                                    "description": "Format for the response"
                                }
                            },
                            "required": ["query"]
                        }
                    }
                }
            },
            "responses": {
                "200": {
                    "description": "Query executed successfully",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/QueryResponse"}
                        }
                    }
                },
                "400": {
                    "description": "Bad request",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/Error"}
                        }
                    }
                },
                "401": {
                    "description": "Unauthorized",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/Error"}
                        }
                    }
                },
                "500": {
                    "description": "Internal server error",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/Error"}
                        }
                    }
                }
            }
        }
    }
    
    # Add tools endpoint
    schema["paths"]["/tools"] = {
        "get": {
            "summary": "List Available Tools",
            "description": "Get list of all available CRM tools",
            "operationId": "list_tools",
            "security": [{"bearerAuth": []}],
            "responses": {
                "200": {
                    "description": "List of available tools",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "tools": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "name": {"type": "string"},
                                                "description": {"type": "string"},
                                                "parameters": {"type": "object"}
                                            }
                                        }
                                    },
                                    "server_info": {"type": "object"}
                                }
                            }
                        }
                    }
                },
                "401": {
                    "description": "Unauthorized",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/Error"}
                        }
                    }
                }
            }
        },
        "post": {
            "summary": "Execute Tool",
            "description": "Execute a specific CRM tool",
            "operationId": "execute_tool",
            "security": [{"bearerAuth": []}],
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "name": {
                                    "type": "string",
                                    "description": "Name of the tool to execute"
                                },
                                "arguments": {
                                    "type": "object",
                                    "description": "Arguments for the tool"
                                }
                            },
                            "required": ["name"]
                        }
                    }
                }
            },
            "responses": {
                "200": {
                    "description": "Tool executed successfully",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/ToolResponse"}
                        }
                    }
                },
                "400": {
                    "description": "Bad request",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/Error"}
                        }
                    }
                },
                "401": {
                    "description": "Unauthorized", 
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/Error"}
                        }
                    }
                },
                "500": {
                    "description": "Internal server error",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/Error"}
                        }
                    }
                }
            }
        }
    }
    
    # Generate individual tool endpoints from MCP tools
    for tool in tools:
        tool_name = tool.name
        safe_name = tool_name.replace("_", "-")
        path = f"/tools/{safe_name}"
        
        # Create individual tool endpoint
        schema["paths"][path] = {
            "post": {
                "summary": f"Execute {tool.name}",
                "description": tool.description,
                "operationId": f"execute_{tool_name}",
                "security": [{"bearerAuth": []}],
                "tags": ["CRM Tools"],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": tool.inputSchema if tool.inputSchema else {"type": "object"}
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": f"{tool.name} executed successfully",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ToolResponse"}
                            }
                        }
                    },
                    "400": {
                        "description": "Bad request",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Error"}
                            }
                        }
                    },
                    "401": {
                        "description": "Unauthorized",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Error"}
                            }
                        }
                    },
                    "500": {
                        "description": "Internal server error",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Error"}
                            }
                        }
                    }
                }
            }
        }
    
    return schema


def save_openapi_schema(schema: Dict[str, Any], output_path: str = "openapi.yaml"):
    """Save OpenAPI schema to YAML file"""
    import yaml
    
    with open(output_path, 'w') as f:
        yaml.dump(schema, f, default_flow_style=False, sort_keys=False)
    
    print(f"OpenAPI schema saved to {output_path}")


async def main():
    """Generate and save OpenAPI schema"""
    schema = await generate_openapi_schema()
    save_openapi_schema(schema)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())