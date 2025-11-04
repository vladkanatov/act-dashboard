"""
Entry point for the application. After refactor this file is a small runner that
loads the FastAPI `app` from the `app` package.
"""
import uvicorn
import argparse
import sys


def main():
    parser = argparse.ArgumentParser(description='Instagram Dashboard API')
    parser.add_argument('--debug', action='store_true', 
                        help='Run in debug mode with mock API responses (no real API calls)')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8000, help='Port to bind to')
    
    args = parser.parse_args()
    
    # Set debug mode in config before importing app
    if args.debug:
        import app.core.config as config
        config.DEBUG_MODE = True
        print("🔧 DEBUG MODE ENABLED - Using mock API responses")
    
    # the FastAPI object is created in the package `app`
    uvicorn.run("app:app", host=args.host, port=args.port, log_level="debug")


if __name__ == "__main__":
    main()