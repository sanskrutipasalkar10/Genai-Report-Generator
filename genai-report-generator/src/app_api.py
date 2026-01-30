import sys
import os
import shutil
import logging
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles # 🟢 ADDED THIS IMPORT

# --- 1. SETUP PATHS & LOGGING ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

# Import the existing pipeline logic
from scripts.generate_full_report import main as run_pipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("API")

# Define Data Directories
RAW_DIR = os.path.join(project_root, "data", "raw")
ARTIFACTS_DIR = os.path.join(project_root, "data", "artifacts")
os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(ARTIFACTS_DIR, exist_ok=True)

# --- 2. INITIALIZE APP ---
app = FastAPI(title="GenAI Report Engine API", version="2.0")

# Enable CORS (Allows React Frontend to talk to this Backend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, set this to ["http://localhost:5173"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🟢 ADDED: MOUNT ARTIFACTS DIRECTORY
# This makes images available at http://localhost:8000/artifacts/...
app.mount("/artifacts", StaticFiles(directory=ARTIFACTS_DIR), name="artifacts")

# --- 3. API ENDPOINTS ---

@app.get("/")
def health_check():
    """Simple check to ensure server is running."""
    return {"status": "online", "system": "GenAI Engine Ready"}

@app.post("/generate")
async def generate_report(file: UploadFile = File(...)):
    """
    Receives file from React -> Runs Python Pipeline -> Returns Report
    """
    try:
        # A. Save the Uploaded File
        file_location = os.path.join(RAW_DIR, file.filename)
        logger.info(f"📥 API Received file: {file.filename}")
        
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # B. Run the AI Pipeline (The Heavy Lifting)
        logger.info("🤖 Starting GenAI Analysis...")
        try:
            # Calls the main() function from generate_full_report.py
            run_pipeline(file_location)
        except Exception as e:
            logger.error(f"Pipeline Execution Failed: {e}")
            raise HTTPException(status_code=500, detail=f"AI Engine Error: {str(e)}")

        # C. Verify Output Files Exist
        report_md_path = os.path.join(ARTIFACTS_DIR, f"{file.filename}_report.md")
        
        if not os.path.exists(report_md_path):
            raise HTTPException(status_code=500, detail="Analysis finished, but no report file was found.")

        # D. Read Markdown Content
        with open(report_md_path, "r", encoding="utf-8") as f:
            markdown_content = f.read()

        logger.info("✅ Report Generated Successfully.")

        # E. Return JSON to React
        return {
            "status": "success",
            "filename": file.filename,
            "markdown_content": markdown_content,
            "pdf_download_url": f"/download/{file.filename}_report.pdf"
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"❌ Critical API Error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/download/{filename}")
async def download_file(filename: str):
    """
    Allows React to download the generated PDF
    """
    file_path = os.path.join(ARTIFACTS_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type='application/pdf', filename=filename)
    
    return JSONResponse(status_code=404, content={"error": "File not found"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)