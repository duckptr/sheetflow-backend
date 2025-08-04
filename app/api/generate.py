from fastapi import APIRouter, UploadFile, File
from fastapi.responses import StreamingResponse, JSONResponse
import pandas as pd
from io import BytesIO
from datetime import datetime

router = APIRouter()

# 사용자 컬럼 → 내부 분석용 컬럼 매핑
COLUMN_MAPPING = {
    "codes": "제품코드",
    "testdate": "준비일",
    "shipdate": "출하일",
    "serialst": "시작시리얼",
    "serialsp": "종료시리얼",
}

@router.post("/generate_excel")
async def generate_excel(file: UploadFile = File(...)):
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

        # 전체 정렬 (시리얼/날짜 없으면 뒤로)
        df_sorted = df.sort_values(
            by=["제품코드", "준비일", "출하일", "시작시리얼", "종료시리얼"],
            ascending=[True, True, True, True, True],
            na_position="last"
        )

        # 엑셀로 저장
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_sorted.to_excel(writer, index=False, sheet_name="SortedData")
        output.seek(0)

        # 파일명 생성
        filename = f"sorted_serials_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except Exception as e:
        import traceback
        print("❌ generate_excel 오류:", e)
        print(traceback.format_exc())
        return JSONResponse(status_code=500, content={"error": str(e)})
