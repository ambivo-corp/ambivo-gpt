#!/usr/bin/env python3
"""
CLI for Ambivo GPT Actions Server
"""

import argparse
import asyncio
import logging
import sys
import subprocess
from server import GPTActionsServer
from schema_generator import generate_openapi_schema, save_openapi_schema


def setup_logging(level=logging.INFO):
    """Setup logging configuration"""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Ambivo GPT Actions Server for ChatGPT integration"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Server command
    server_parser = subparsers.add_parser('serve', help='Start the GPT Actions server')
    server_parser.add_argument(
        '--host', 
        default='localhost',
        help='Host to bind to (default: localhost)'
    )
    server_parser.add_argument(
        '--port', 
        type=int, 
        default=8080,
        help='Port to bind to (default: 8080)'
    )
    server_parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    # Schema generation command
    schema_parser = subparsers.add_parser('generate-schema', help='Generate OpenAPI schema')
    schema_parser.add_argument(
        '--output', '-o',
        default='openapi.yaml',
        help='Output file for OpenAPI schema (default: openapi.yaml)'
    )
    schema_parser.add_argument(
        '--format',
        choices=['yaml', 'json'],
        default='yaml',
        help='Output format (default: yaml)'
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Setup logging
    log_level = logging.DEBUG if getattr(args, 'verbose', False) else logging.INFO
    setup_logging(log_level)
    
    if args.command == 'serve':
        # Start the FastAPI server (proper async implementation)
        try:
            print(f"Starting Ambivo GPT Actions FastAPI server on {args.host}:{args.port}")
            print(f"API documentation: http://{args.host}:{args.port}/docs")
            print(f"OpenAPI spec: http://{args.host}:{args.port}/openapi.json")
            print("Press Ctrl+C to stop the server")
            
            # Use FastAPI server instead
            try:
                import uvicorn
                from main import app
            except ImportError as e:
                print(f"FastAPI dependencies not installed: {e}")
                print("Installing required dependencies...")
                import subprocess
                subprocess.check_call([sys.executable, "-m", "pip", "install", "fastapi>=0.104.0", "uvicorn>=0.24.0"])
                
                # Retry import
                import uvicorn
                from main import app
            
            uvicorn.run(
                app, 
                host=args.host, 
                port=args.port,
                log_level="info" if getattr(args, 'verbose', False) else "warning"
            )
            
        except KeyboardInterrupt:
            print("\nServer stopped by user")
        except Exception as e:
            print(f"Error starting server: {e}")
            sys.exit(1)
    
    elif args.command == 'generate-schema':
        # Generate OpenAPI schema
        try:
            print("Generating OpenAPI schema from MCP tools...")
            
            async def generate_and_save():
                schema = await generate_openapi_schema()
                
                if args.format == 'json':
                    import json
                    output_file = args.output.replace('.yaml', '.json').replace('.yml', '.json')
                    with open(output_file, 'w') as f:
                        json.dump(schema, f, indent=2)
                    print(f"OpenAPI schema saved to {output_file}")
                else:
                    save_openapi_schema(schema, args.output)
            
            asyncio.run(generate_and_save())
            
        except Exception as e:
            print(f"Error generating schema: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()