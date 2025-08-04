from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ✅ app/api 폴더 안의 라우터들 import
from app.api import upload, result, grouped, sort, generate

app = FastAPI(
    title="SheetFlow Backend",
    description="엑셀 분석 및 자동화 백엔드 API",
    version="1.0.0"
)

# ✅ CORS 설정 (Flutter 등 외부 요청 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발 단계에서는 전체 허용, 운영에서는 도메인 제한 권장
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ API 라우터 등록
app.include_router(upload.router, prefix="/upload", tags=["Upload"])
app.include_router(result.router, prefix="/result", tags=["Result"])
app.include_router(grouped.router, prefix="/group", tags=["Group"])
app.include_router(sort.router, prefix="/sort", tags=["Sort"])
app.include_router(generate.router, prefix="/generate", tags=["Generate"])

# ✅ 헬스 체크용 기본 엔드포인트
@app.get("/")
async def root():
    return {"message": "Sheetflow backend is alive!"}
