#!/usr/bin/env python3
"""
FastAPI-based GPT Actions Server - Proper async implementation
"""

import json
import logging
import os
import sys
from datetime import datetime, UTC
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

# Version timestamp - automatically updated on git push
VERSION_TIMESTAMP = "2025-07-31T02:50:00Z"

# Import local MCP core functionality
from mcp_core import handle_list_tools, handle_call_tool, api_client


# Pydantic models
class QueryRequest(BaseModel):
    query: str
    response_format: str = "both"


class ToolRequest(BaseModel):
    name: str
    arguments: Dict[str, Any] = {}


# Create FastAPI app
app = FastAPI(
    title="Ambivo CRM API",
    description="API for accessing and querying Ambivo CRM data using natural language and direct tool calls",
    version="1.0.0",
    openapi_version="3.1.0",
    servers=[
        {"url": "https://gpt.ambivo.com", "description": "Production server"}
    ]
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Auth dependency
async def get_auth_token(authorization: Optional[str] = Header(None)) -> str:
    """Extract and validate auth token from Authorization header"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer token required")
    
    token = authorization[7:]  # Remove "Bearer " prefix
    if not token:
        raise HTTPException(status_code=401, detail="Token cannot be empty")
    
    return token


# Routes
@app.get("/")
async def root():
    """Root endpoint - API documentation"""
    return {
        "name": "Ambivo GPT Actions API",
        "version": "1.0.0",
        "description": "Direct API for ChatGPT integration with Ambivo CRM data",
        "endpoints": {
            "GET /": "API documentation",
            "GET /.well-known/ai-plugin.json": "AI plugin manifest",
            "GET /openapi.json": "OpenAPI specification (JSON)",
            "GET /openapi.yaml": "OpenAPI specification (YAML)",
            "GET /health": "Health check",
            "GET /tools": "List available tools",
            "POST /tools": "Execute a specific tool",
            "POST /query": "Natural language query"
        },
        "authentication": {
            "type": "Bearer Token",
            "description": "Include JWT token in Authorization header"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        tools = await handle_list_tools()
        tool_names = [tool.name for tool in tools]
        
        return {
            "status": "healthy",
            "timestamp": datetime.now(UTC).isoformat(),
            "available_tools": tool_names,
            "server_type": "gpt_actions_fastapi",
            "version": VERSION_TIMESTAMP,
            "deployment_info": {
                "version_timestamp": VERSION_TIMESTAMP,
                "build_time": datetime.now(UTC).isoformat()
            }
        }
    except Exception as e:
        logging.error(f"Health check error: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@app.get("/openapi.json")
@app.post("/openapi.json")
async def get_openapi_schema():
    """Get OpenAPI schema - FastAPI generates this automatically"""
    schema = app.openapi()
    
    # Ensure the servers section is exactly what ChatGPT expects
    schema["servers"] = [
        {
            "url": "https://gpt.ambivo.com",
            "description": "Production server"
        }
    ]
    
    # Ensure OpenAPI version is 3.1.0 (required by ChatGPT)
    schema["openapi"] = "3.1.0"
    
    # Add security scheme for Bearer tokens
    if "components" not in schema:
        schema["components"] = {}
    if "securitySchemes" not in schema["components"]:
        schema["components"]["securitySchemes"] = {}
    
    schema["components"]["securitySchemes"]["bearerAuth"] = {
        "type": "http",
        "scheme": "bearer"
    }
    
    # Add global security requirement
    schema["security"] = [{"bearerAuth": []}]
    
    return schema


@app.get("/openapi.yaml")
async def get_openapi_yaml():
    """Get OpenAPI schema in YAML format"""
    import yaml
    schema = app.openapi()
    return Response(
        content=yaml.dump(schema, default_flow_style=False),
        media_type="application/x-yaml"
    )


@app.get("/.well-known/ai-plugin.json") 
async def get_ai_plugin():
    """AI plugin manifest for ChatGPT"""
    return {
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
            "url": "https://gpt.ambivo.com/openapi.json"
        },
        "logo_url": "https://ambivo.com/logo.png",
        "contact_email": "dev@ambivo.com",
        "legal_info_url": "https://ambivo.com/legal"
    }


@app.post("/query", operation_id="queryData", summary="Query CRM data", description="Execute natural language query against CRM data")
@app.get("/query", operation_id="queryDataGet", summary="Query CRM data (GET)", description="Execute natural language query via GET parameters")
async def natural_language_query(
    request: QueryRequest = None,
    token: str = Depends(get_auth_token),
    query: str = None,
    response_format: str = "both"
):
    """Execute natural language query"""
    try:
        # Handle both POST (JSON body) and GET (query parameters)
        if request:
            # POST request with JSON body
            query_text = request.query
            format_type = request.response_format
        else:
            # GET request with query parameters
            query_text = query
            format_type = response_format
            
        if not query_text:
            raise HTTPException(status_code=400, detail="Query parameter is required")
        
        # Set auth token for this request
        original_token = api_client.auth_token
        api_client.set_auth_token(token)
        
        try:
            # Call the MCP tool directly (no event loop issues!)
            result = await handle_call_tool('natural_query', {
                'query': query_text,
                'response_format': format_type
            })
            
            # Format response
            response_text = ""
            for content in result:
                response_text += content.text + "\n"
            
            return {
                "query": query_text,
                "result": response_text.strip(),
                "response_format": format_type,
                "timestamp": datetime.now(UTC).isoformat(),
                "success": True
            }
            
        finally:
            # Restore original token
            if original_token:
                api_client.auth_token = original_token
            else:
                api_client.auth_token = None
                
    except Exception as e:
        logging.error(f"Natural query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tools")
async def list_tools(token: str = Depends(get_auth_token)):
    """List available tools"""
    try:
        # Set auth token for this request
        original_token = api_client.auth_token
        api_client.set_auth_token(token)
        
        try:
            mcp_tools = await handle_list_tools()
            
            # Convert to OpenAI function calling format
            tools = []
            for tool in mcp_tools:
                tool_def = {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema
                }
                tools.append(tool_def)
            
            return {
                "tools": tools,
                "server_info": {
                    "name": "ambivo-gpt-actions-fastapi",
                    "version": VERSION_TIMESTAMP,
                    "capabilities": ["natural_language_queries", "crm_data_access"]
                }
            }
            
        finally:
            # Restore original token
            if original_token:
                api_client.auth_token = original_token
            else:
                api_client.auth_token = None
                
    except Exception as e:
        logging.error(f"List tools error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tools")
@app.get("/tools/execute")
async def execute_tool(
    request: ToolRequest = None,
    token: str = Depends(get_auth_token),
    name: str = None,
    arguments: str = "{}"
):
    """Execute a specific tool"""
    try:
        # Set auth token for this request
        original_token = api_client.auth_token
        api_client.set_auth_token(token)
        
        try:
            # Call the MCP tool directly
            result = await handle_call_tool(request.name, request.arguments)
            
            # Format response
            response_text = ""
            for content in result:
                response_text += content.text + "\n"
            
            return {
                "result": response_text.strip(),
                "tool_name": request.name,
                "success": True
            }
            
        finally:
            # Restore original token
            if original_token:
                api_client.auth_token = original_token
            else:
                api_client.auth_token = None
                
    except Exception as e:
        logging.error(f"Tool execution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/debug")
async def debug_info():
    """Debug endpoint"""
    return {
        "message": "FastAPI server working",
        "version": VERSION_TIMESTAMP,
        "timestamp": datetime.now(UTC).isoformat(),
        "endpoints": {
            "health": "/health",
            "openapi": "/openapi.json", 
            "query": "/query",
            "tools": "/tools"
        }
    }


# For running with uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)