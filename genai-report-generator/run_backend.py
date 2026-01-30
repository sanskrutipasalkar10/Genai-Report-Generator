import sys
import os
import uvicorn

# 1. Force the current script's directory (Root) into Python's path
root_dir = os.path.dirname(os.path.abspath(__file__))
if root_dir not in sys.path:
    sys.path.append(root_dir)

print(f"📂 Execution Path: {root_dir}")

# 2. Import the app object DIRECTLY
try:
    # This looks for src/app_api.py and imports the 'app' variable
    from src.app_api import app
    print("✅ Successfully imported FastAPI app.")
except ImportError as e:
    print(f"\n❌ CRITICAL IMPORT ERROR: {e}")
    print("---------------------------------------------------")
    print("Troubleshooting steps:")
    print("1. Are you in the 'genai-report-generator' folder?")
    print("2. Does 'src/app_api.py' exist?")
    print("3. Does 'src/__init__.py' exist?")
    print("---------------------------------------------------")
    sys.exit(1)

if __name__ == "__main__":
    print("🚀 Starting Server on Port 8000...")
    # Serve the app
    uvicorn.run(app, host="0.0.0.0", port=8000)