"""
Debug runner for PyCharm
This file allows you to run the FastAPI app with PyCharm's debugger
"""
import uvicorn

if __name__ == "__main__":
    # Run with reload disabled for debugging
    # You can set breakpoints in your code and they will work
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=False,  # Disable reload for debugging
        log_level="info"
    )