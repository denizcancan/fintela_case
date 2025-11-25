"""Simple script to run the FastAPI server."""

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "case_study.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload on code changes
    )

