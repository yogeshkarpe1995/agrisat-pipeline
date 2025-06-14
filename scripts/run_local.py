
#!/usr/bin/env python3
"""
Local development runner for Satellite Agriculture Monitoring Pipeline.
This script helps run the services locally with proper setup.
"""

import os
import sys
import subprocess
import time
import argparse
from pathlib import Path

def load_env_file():
    """Load environment variables from .env file if it exists."""
    env_file = Path(".env")
    if env_file.exists():
        print("Loading environment variables from .env file...")
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
    else:
        print("Warning: .env file not found. Copy .env.example to .env and configure it.")

def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import flask
        import rasterio
        import numpy
        import sqlalchemy
        import requests
        print("✓ All required dependencies are installed")
        return True
    except ImportError as e:
        print(f"✗ Missing dependency: {e}")
        print("Run: pip install -r requirements.txt")
        return False

def setup_database():
    """Initialize database if it doesn't exist."""
    db_file = Path("satellite_monitoring.db")
    if not db_file.exists():
        print("Creating database...")
        try:
            subprocess.run([sys.executable, "create_database.py"], check=True)
            print("✓ Database created successfully")
        except subprocess.CalledProcessError:
            print("✗ Failed to create database")
            return False
    else:
        print("✓ Database already exists")
    return True

def run_api_server():
    """Run the API server."""
    print("Starting API server on http://0.0.0.0:5000...")
    try:
        subprocess.run([sys.executable, "api_server.py"], check=True)
    except KeyboardInterrupt:
        print("\nAPI server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"API server failed: {e}")

def run_pipeline():
    """Run the satellite processing pipeline."""
    print("Starting satellite processing pipeline...")
    try:
        subprocess.run([sys.executable, "main.py"], check=True)
        print("✓ Pipeline completed successfully")
    except KeyboardInterrupt:
        print("\nPipeline stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"Pipeline failed: {e}")

def main():
    """Main function to handle command line arguments and run services."""
    parser = argparse.ArgumentParser(description="Run Satellite Agriculture Monitoring Pipeline locally")
    parser.add_argument("--service", choices=["api", "pipeline", "both"], default="both",
                      help="Which service to run (default: both)")
    parser.add_argument("--skip-setup", action="store_true",
                      help="Skip dependency and database setup checks")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Satellite Agriculture Monitoring Pipeline - Local Runner")
    print("=" * 60)
    
    # Load environment variables
    load_env_file()
    
    if not args.skip_setup:
        # Check dependencies
        if not check_dependencies():
            sys.exit(1)
        
        # Setup database
        if not setup_database():
            sys.exit(1)
    
    # Create output directory
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    try:
        if args.service == "api":
            run_api_server()
        elif args.service == "pipeline":
            run_pipeline()
        elif args.service == "both":
            print("\nRunning both services...")
            print("Note: API server will run in the foreground.")
            print("Open a new terminal and run 'python main.py' to start the pipeline.")
            print("\nPress Ctrl+C to stop the API server\n")
            run_api_server()
            
    except KeyboardInterrupt:
        print("\nShutting down services...")
    
    print("Done!")

if __name__ == "__main__":
    main()
