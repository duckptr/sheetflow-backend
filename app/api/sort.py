from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse
import pandas as pd
from io import BytesIO

router = APIRouter()

# 사용자 컬럼 → 내부 분석용 컬럼 매핑
COLUMN_MAPPING = {
    "codes": "제품코드",
    "testdate": "준비일",
    "shipdate": "출하일",
    "serialst": "시작시리얼",
    "serialsp": "종료시리얼",
}

@router.post("/sort_excel")
async def sort_excel(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        df = pd.read_excel(BytesIO(contents))

        # 원본 컬럼 소문자화
        df.columns = [col.lower() for col in df.columns]

        # 매핑 적용
        df = df.rename(columns={k: v for k, v in COLUMN_MAPPING.items() if k in df.columns})

        # 날짜 컬럼 처리
        for date_col in ["준비일", "출하일"]:
            if date_col in df.columns:
                df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
            else:
                df[date_col] = pd.NaT

        # 시리얼 없는 행도 포함 → 대신 뒤로 가게 설정
        df_sorted = df.sort_values(
            by=["제품코드", "준비일", "출하일", "시작시리얼", "종료시리얼"],
            ascending=[True, True, True, True, True],
            na_position="last"
        )

        # JSON 변환
        rows = []
        for _, row in df_sorted.iterrows():
            rows.append({
                "제품코드": row.get("제품코드"),
                "준비일": row["준비일"].strftime("%Y-%m-%d") if pd.notnull(row["준비일"]) else None,
                "출하일": row["출하일"].strftime("%Y-%m-%d") if pd.notnull(row["출하일"]) else None,
                "시작시리얼": str(row["시작시리얼"]).strip() if pd.notnull(row["시작시리얼"]) else None,
                "종료시리얼": str(row["종료시리얼"]).strip() if pd.notnull(row["종료시리얼"]) else None,
            })

        # 미리보기 50행만 반환
        return {"sorted_preview": rows[:50]}

    except Exception as e:
        import traceback
        print("❌ sort_excel 오류:", e)
        print(traceback.format_exc())
        return JSONResponse(status_code=500, content={"error": str(e)})
