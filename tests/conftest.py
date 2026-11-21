import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
os.environ.pop("AI_API_KEY", None)  # force offline demo mode so no real API calls happen
