#!/usr/bin/env python3
"""
Script to generate OpenAPI specification from the FastAPI application.

Usage:
    python -m src.api.generate_openapi
    or
    cd BackendAPI && python -m src.api.generate_openapi

The script will write the current OpenAPI JSON to interfaces/openapi.json
"""
import json
import os
import sys

# Add parent directory to path to allow imports
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.api.main import app

# PUBLIC_INTERFACE
def generate_openapi_spec(output_path: str = None) -> dict:
    """
    Generate and save the OpenAPI specification.
    
    Args:
        output_path: Optional custom output path. Defaults to interfaces/openapi.json
        
    Returns:
        The OpenAPI schema dictionary
    """
    # Get the OpenAPI schema from FastAPI
    openapi_schema = app.openapi()
    
    # Determine output path
    if output_path is None:
        # Default to interfaces/openapi.json relative to project root
        output_dir = os.path.join(project_root, "interfaces")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "openapi.json")
    else:
        # Ensure parent directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
    
    # Write to file with pretty formatting
    with open(output_path, "w") as f:
        json.dump(openapi_schema, f, indent=2)
    
    print(f"✓ OpenAPI specification generated: {output_path}")
    print(f"  Total endpoints: {len(openapi_schema.get('paths', {}))}")
    print(f"  API version: {openapi_schema.get('info', {}).get('version', 'unknown')}")
    
    return openapi_schema


if __name__ == "__main__":
    try:
        schema = generate_openapi_spec()
        sys.exit(0)
    except Exception as e:
        print(f"✗ Error generating OpenAPI spec: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
