"""
Entry point for the application. After refactor this file is a small runner that
loads the FastAPI `app` from the `app` package.
"""
import uvicorn


if __name__ == "__main__":
    # the FastAPI object is created in the package `app`
    uvicorn.run("app:app", host="0.0.0.0", port=8000, log_level="debug")