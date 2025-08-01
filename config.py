#!/usr/bin/env python3
"""
Configuration settings for Ambivo GPT Actions
"""

import os
from typing import Optional

# Default server settings
DEFAULT_HOST = "localhost"
DEFAULT_PORT = 8080

# Environment variable names
ENV_AUTH_TOKEN = "AMBIVO_AUTH_TOKEN"
ENV_API_BASE_URL = "AMBIVO_API_BASE_URL"
ENV_SERVER_HOST = "AMBIVO_GPT_HOST"
ENV_SERVER_PORT = "AMBIVO_GPT_PORT"

# API settings
DEFAULT_API_BASE_URL = "https://api.ambivo.com"

# CORS settings
CORS_ALLOW_ORIGINS = ["*"]
CORS_ALLOW_METHODS = ["GET", "POST", "OPTIONS"]
CORS_ALLOW_HEADERS = ["Content-Type", "Authorization"]

# Rate limiting (requests per minute)
RATE_LIMIT_REQUESTS = 100
RATE_LIMIT_WINDOW = 60  # seconds

# Request timeout (seconds)
REQUEST_TIMEOUT = 30

# Maximum request body size (bytes)
MAX_REQUEST_SIZE = 1024 * 1024  # 1MB


class Config:
    """Configuration class for GPT Actions server"""
    
    def __init__(self):
        self.host = os.getenv(ENV_SERVER_HOST, DEFAULT_HOST)
        self.port = int(os.getenv(ENV_SERVER_PORT, DEFAULT_PORT))
        self.auth_token = os.getenv(ENV_AUTH_TOKEN)
        self.api_base_url = os.getenv(ENV_API_BASE_URL, DEFAULT_API_BASE_URL)
        
        # Server settings
        self.cors_allow_origins = CORS_ALLOW_ORIGINS
        self.cors_allow_methods = CORS_ALLOW_METHODS
        self.cors_allow_headers = CORS_ALLOW_HEADERS
        
        # Rate limiting
        self.rate_limit_requests = RATE_LIMIT_REQUESTS
        self.rate_limit_window = RATE_LIMIT_WINDOW
        
        # Timeouts
        self.request_timeout = REQUEST_TIMEOUT
        self.max_request_size = MAX_REQUEST_SIZE
    
    def get_server_url(self) -> str:
        """Get the full server URL"""
        return f"http://{self.host}:{self.port}"
    
    def validate(self) -> bool:
        """Validate configuration"""
        if not self.auth_token:
            print(f"Warning: No auth token found in environment variable {ENV_AUTH_TOKEN}")
            return False
        return True


# Global config instance
config = Config()