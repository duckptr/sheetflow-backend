from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import upload, result

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(upload.router, prefix="/upload", tags=["Upload"])
app.include_router(result.router, prefix="/result", tags=["Result"])

@app.get("/")
async def root():
    return {"message": "Sheetflow backend is alive!"}
