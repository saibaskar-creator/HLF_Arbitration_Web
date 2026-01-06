import sys
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router as api_router

# Add the project root to sys.path so we can import 'src'
# Assuming backend/main.py is one level down from HLF_Arbitration_Web
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

app = FastAPI(title="HLF Arbitration API", version="0.1.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.staticfiles import StaticFiles

# Create temp_uploads if not exists
UPLOAD_DIR = os.path.join(BASE_DIR, "backend", "temp_uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

app.include_router(api_router, prefix="/api")

# Mount static files to serve PDFs
app.mount("/api/files", StaticFiles(directory=UPLOAD_DIR), name="files")

@app.get("/")
def read_root():
    return {"message": "HLF Arbitration API is running"}
