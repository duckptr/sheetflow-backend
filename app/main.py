from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ✅ 라우터들
from app.api import upload, result, grouped, sort, generate, analyze
from app.workers.watchdog_worker import start_watchdog  # ✅ 감시기 import

app = FastAPI(
    title="SheetFlow Backend",
    description="엑셀 분석 및 자동화 백엔드 API",
    version="1.0.0"
)

# ✅ CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발 단계에서는 전체 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ 라우터 등록
app.include_router(upload.router, prefix="/upload", tags=["Upload"])
app.include_router(result.router, prefix="/result", tags=["Result"])
app.include_router(grouped.router, prefix="/group", tags=["Group"])
app.include_router(sort.router, prefix="/sort", tags=["Sort"])
app.include_router(generate.router, prefix="/generate", tags=["Generate"])
app.include_router(analyze.router, prefix="/analyze", tags=["Analyze"])

# ✅ 앱 시작 시 감시기 실행
@app.on_event("startup")
async def startup_event():
    start_watchdog()

# ✅ 기본 라우트 (헬스 체크용)
@app.get("/")
async def root():
    return {"message": "Sheetflow backend is alive!"}
