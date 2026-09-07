"""Private preview compatibility entrypoint after approved-theme integration.

The existing review service keeps its address, but now serves the normal app.
No comparison middleware, runtime art replacement or A/B/C controls are loaded.
Historical prototype source remains available for reference, not execution.
"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import uvicorn
from main import app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=51355, log_level="warning")
