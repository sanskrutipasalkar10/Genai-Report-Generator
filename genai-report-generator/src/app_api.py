import sys
import os
import shutil
import logging
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles 

# --- 1. SETUP PATHS ---
current_dir = os.path.dirname(os.path.abspath(__file__)) 
project_root = os.path.dirname(current_dir)            

# Fix import for the pipeline
scripts_dir = os.path.join(project_root, "scripts")
if scripts_dir not in sys.path:
    sys.path.append(scripts_dir)

try:
    from generate_full_report import main as run_pipeline
except ImportError:
    if project_root not in sys.path:
        sys.path.append(project_root)
    from scripts.generate_full_report import main as run_pipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("API")

# Define Directories
RAW_DIR = os.path.join(project_root, "data", "raw")
ARTIFACTS_DIR = os.path.join(project_root, "data", "artifacts")

os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(ARTIFACTS_DIR, exist_ok=True)

# --- 2. INITIALIZE APP ---
app = FastAPI(title="GenAI Report Engine API", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🟢 DEBUG: PRINT FILES IN ARTIFACTS FOLDER
print(f"\n📂 MOUNTING ARTIFACTS: {ARTIFACTS_DIR}")
if os.path.exists(ARTIFACTS_DIR):
    files = os.listdir(ARTIFACTS_DIR)
    print(f"👀 Found {len(files)} files: {files[:5]}...") # Print first 5 files
    app.mount("/artifacts", StaticFiles(directory=ARTIFACTS_DIR), name="artifacts")
else:
    print("❌ ARTIFACTS DIRECTORY DOES NOT EXIST!")

# --- 3. ENDPOINTS ---
@app.get("/")
def health_check():
    return {"status": "online"}

@app.post("/generate")
async def generate_report(file: UploadFile = File(...)):
    try:
        file_location = os.path.join(RAW_DIR, file.filename)
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        logger.info("🤖 Starting Analysis...")
        run_pipeline(file_location)

        # Check for report
        report_md_path = os.path.join(ARTIFACTS_DIR, f"{file.filename}_report.md")
        if not os.path.exists(report_md_path):
            raise HTTPException(status_code=500, detail="Report generation failed. No .md file found.")

        with open(report_md_path, "r", encoding="utf-8") as f:
            markdown_content = f.read()

        return {
            "status": "success",
            "filename": file.filename,
            "markdown_content": markdown_content,
            "pdf_download_url": f"/download/{file.filename}_report.pdf"
        }
    except Exception as e:
        logger.error(f"API Error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/download/{filename}")
async def download_file(filename: str):
    file_path = os.path.join(ARTIFACTS_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type='application/pdf', filename=filename)
    return JSONResponse(status_code=404, content={"error": "File not found"})