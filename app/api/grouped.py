from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse
import pandas as pd
from io import BytesIO

router = APIRouter()

# 사용자 컬럼명을 분석용 내부 명칭으로 매핑
COLUMN_MAPPING = {
    "codes": "제품코드",
    "testdate": "준비일",     # 준비 날짜 (Test Date)
    "shipdate": "출하일",     # 출하 날짜 (Ship Date)
    "serialst": "시작시리얼",
    "serialsp": "종료시리얼",
}

@router.post("/")
async def group_excel(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        df = pd.read_excel(BytesIO(contents))

        # ✅ 소문자 변환 후 매핑
        original_columns = df.columns
        df.columns = [col.lower() for col in df.columns]
        df = df.rename(columns={k: v for k, v in COLUMN_MAPPING.items() if k in df.columns})

        # ✅ 필수 컬럼 확인
        required = list(COLUMN_MAPPING.values())
        for col in required:
            if col not in df.columns:
                return JSONResponse(status_code=400, content={
                    "error": f"❌ 필수 컬럼 누락: {col}",
                    "hint": f"현재 컬럼들: {original_columns.tolist()}"
                })

        # ✅ 날짜 변환
        df["준비일"] = pd.to_datetime(df["준비일"], errors="coerce")
        df["출하일"] = pd.to_datetime(df["출하일"], errors="coerce")

        # ✅ 시리얼이 존재하는 행만 필터링
        df = df[df["시작시리얼"].notnull() & df["종료시리얼"].notnull()]

        grouped_result = []
        warnings = []

        # ✅ 제품코드 기준 그룹화
        for code, group in df.groupby("제품코드"):
            logs = []
            for _, row in group.sort_values("출하일").iterrows():
                logs.append({
                    "test_date": row["준비일"].strftime("%Y-%m-%d") if pd.notnull(row["준비일"]) else None,
                    "ship_date": row["출하일"].strftime("%Y-%m-%d") if pd.notnull(row["출하일"]) else None,
                    "serial_start": str(row["시작시리얼"]).strip(),
                    "serial_end": str(row["종료시리얼"]).strip(),
                })

            grouped_result.append({
                "product_code": code,
                "serial_logs": logs,
            })

        return JSONResponse(content={
            "grouped_by_product": grouped_result,
            "warnings": warnings
        })

    except Exception as e:
        print(f"🚨 전체 처리 실패: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})
