from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import upload, result, grouped, export  # ✅ export 라우터도 import

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ 각 API 라우터 등록
app.include_router(upload.router, prefix="/upload", tags=["Upload"])
app.include_router(result.router, prefix="/result", tags=["Result"])
app.include_router(grouped.router, prefix="/group", tags=["Group"])
app.include_router(export.router, prefix="/export", tags=["Export"])  # ✅ 추가된 export 라우터

@app.get("/")
async def root():
    return {"message": "Sheetflow backend is alive!"}
