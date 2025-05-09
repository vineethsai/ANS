"""
Script to run the Agent Name Service server.
"""
import uvicorn
from ans.db.init_db import init_database

def main():
    """Initialize database and start the server."""
    # Initialize database
    init_database()

    # Start server
    uvicorn.run(
        "ans.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

if __name__ == "__main__":
    main() 