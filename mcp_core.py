#!/usr/bin/env python3
"""
Core MCP Server functionality extracted for GPT Actions
Simplified version without full MCP dependencies
"""

import asyncio
import json
import logging
import os
import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

import httpx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ambivo-gpt.mcp")


@dataclass
class Tool:
    """Simplified Tool definition"""
    name: str
    description: str
    inputSchema: Dict[str, Any]


@dataclass 
class TextContent:
    """Simplified TextContent definition"""
    type: str
    text: str


class AmbivoAPIClient:
    """Client for interacting with Ambivo API endpoints"""

    def __init__(self, base_url: str = None, auth_token: Optional[str] = None):
        self.base_url = (base_url or os.getenv("AMBIVO_BASE_URL", "https://goferapi.ambivo.com")).rstrip("/")
        self.auth_token = auth_token or os.getenv("AMBIVO_AUTH_TOKEN")
        self.timeout = float(os.getenv("AMBIVO_TIMEOUT", "30.0"))
        self.max_retries = int(os.getenv("AMBIVO_MAX_RETRIES", "3"))
        self.client = httpx.AsyncClient(timeout=self.timeout)
        self.logger = logging.getLogger("ambivo-gpt.client")

    def set_auth_token(self, token: str):
        """Set the authentication token"""
        if not token or len(token) < 10:
            raise ValueError("Invalid token format")
        self.auth_token = token
        self.logger.info("Authentication token set successfully")

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests"""
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        return headers

    async def _make_request_with_retry(
        self, method: str, url: str, **kwargs
    ) -> httpx.Response:
        """Make HTTP request with retry logic"""
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                response = await self.client.request(method, url, **kwargs)
                return response
            except (httpx.TimeoutException, httpx.ConnectError, httpx.ReadError) as e:
                last_exception = e
                if attempt < self.max_retries:
                    wait_time = 2**attempt  # Exponential backoff
                    self.logger.warning(
                        f"Request attempt {attempt + 1} failed, retrying in {wait_time}s: {e}"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    self.logger.error(
                        f"All {self.max_retries + 1} request attempts failed"
                    )
                    raise

        raise last_exception

    async def natural_query(
        self, query: str, response_format: str = "both", enable_memory: Optional[bool] = None, session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute a natural language query against entity data"""
        
        # Basic validation
        if not query or len(query.strip()) == 0:
            raise ValueError("Query cannot be empty")
        
        if len(query) > 1000:
            raise ValueError("Query too long. Maximum length: 1000")

        if response_format not in ["table", "natural", "both"]:
            raise ValueError(
                "Invalid response_format. Must be 'table', 'natural', or 'both'"
            )

        payload = {"query": query, "response_format": response_format}
        
        # Add optional parameters if provided
        if enable_memory is not None:
            payload["enable_memory"] = enable_memory
        if session_id is not None:
            payload["session_id"] = session_id
        url = f"{self.base_url}/entity/natural_query"

        try:
            self.logger.info(f"Executing natural query: {query[:100]}...")
            start_time = time.time()

            response = await self._make_request_with_retry(
                "POST", url, json=payload, headers=self._get_headers()
            )

            elapsed_time = time.time() - start_time
            self.logger.info(f"Natural query completed in {elapsed_time:.2f}s")

            response.raise_for_status()
            result = response.json()

            self.logger.debug(f"API response: {json.dumps(result, indent=2)[:500]}...")
            return result

        except httpx.TimeoutException as e:
            self.logger.error(f"Natural query timeout: {e}")
            raise Exception(f"Request timeout after {self.timeout}s")
        except httpx.HTTPStatusError as e:
            self.logger.error(
                f"Natural query HTTP error: {e.response.status_code} - {e.response.text}"
            )
            raise
        except Exception as e:
            self.logger.error(f"Natural query unexpected error: {e}")
            raise

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


# Global client instance
api_client = AmbivoAPIClient()


async def handle_list_tools() -> List[Tool]:
    """List available tools"""
    return [
        Tool(
            name="natural_query",
            description="Execute natural language queries against Ambivo entity data. "
            "This tool processes natural language queries and returns structured data "
            "about leads, contacts, opportunities, and other entities.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural language query describing what data you want to retrieve. "
                        "Examples: 'Show me leads created this week', 'Find contacts with gmail addresses', "
                        "'List opportunities worth more than $10,000'",
                    },
                    "response_format": {
                        "type": "string",
                        "enum": ["table", "natural", "both"],
                        "default": "both",
                        "description": "Format of the response: 'table' for structured data, "
                        "'natural' for natural language description, 'both' for both formats",
                    },
                    "enable_memory": {
                        "type": "boolean",
                        "description": "Optional flag to enable memory for the query session",
                    },
                    "session_id": {
                        "type": "string",
                        "description": "Optional session identifier for memory management",
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="set_auth_token",
            description="Set the authentication token for API requests. "
            "This must be called before using other tools to authenticate with the Ambivo API.",
            inputSchema={
                "type": "object",
                "properties": {
                    "token": {
                        "type": "string",
                        "description": "JWT Bearer token for authentication with Ambivo API",
                    }
                },
                "required": ["token"],
            },
        ),
    ]


async def handle_call_tool(
    name: str, arguments: Dict[str, Any] | None
) -> List[TextContent]:
    """Handle tool calls"""
    if arguments is None:
        arguments = {}

    start_time = time.time()
    logger.info(f"Tool call started: {name}")

    try:
        if name == "set_auth_token":
            token = arguments.get("token")
            if not token:
                return [
                    TextContent(
                        type="text", text="Error: Authentication token is required"
                    )
                ]

            # Set token
            api_client.set_auth_token(token)

            return [
                TextContent(
                    type="text",
                    text="Authentication token set successfully. You can now use other tools to query the Ambivo API.",
                )
            ]

        elif name == "natural_query":
            if not api_client.auth_token:
                return [
                    TextContent(
                        type="text",
                        text="Error: Authentication required. Please use the 'set_auth_token' tool first.",
                    )
                ]

            query = arguments.get("query")
            if not query:
                return [
                    TextContent(
                        type="text", text="Error: Query parameter is required"
                    )
                ]

            response_format = arguments.get("response_format", "both")
            enable_memory = arguments.get("enable_memory")
            session_id = arguments.get("session_id")

            try:
                result = await api_client.natural_query(query, response_format, enable_memory, session_id)
                return [
                    TextContent(
                        type="text",
                        text=f"Natural Query Results:\n\n{json.dumps(result, indent=2)}",
                    )
                ]
            except httpx.HTTPStatusError as e:
                error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
                return [TextContent(type="text", text=f"API Error: {error_msg}")]
            except Exception as e:
                return [
                    TextContent(
                        type="text", text=f"Error executing natural query: {str(e)}"
                    )
                ]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except ValueError as e:
        logger.warning(f"Validation error in tool {name}: {e}")
        return [TextContent(type="text", text=f"Validation Error: {str(e)}")]

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error in tool {name}: {e.response.status_code}")
        error_msg = f"API Error (HTTP {e.response.status_code})"
        try:
            error_detail = e.response.json()
            if "error_code" in error_detail:
                error_msg += f": {error_detail['error_code']}"
        except:
            error_msg += f": {e.response.text[:200]}"

        return [TextContent(type="text", text=error_msg)]

    except Exception as e:
        logger.exception(f"Unexpected error in tool {name}")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]

    finally:
        elapsed_time = time.time() - start_time
        logger.info(f"Tool call completed: {name} in {elapsed_time:.2f}s")