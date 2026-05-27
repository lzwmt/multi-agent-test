#!/usr/bin/env python3
"""Entry point for AI Tarot backend server."""

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=18899,
        reload=False,
        log_level="info",
    )
