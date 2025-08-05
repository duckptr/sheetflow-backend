from fastapi import APIRouter, UploadFile, File
from fastapi.responses import StreamingResponse, JSONResponse
import pandas as pd
from io import BytesIO
from datetime import datetime
from app.utils.formatter import apply_excel_formats

router = APIRouter()

# 허용할 컬럼 목록 (불필요 컬럼 제거용)
ALLOWED_COLUMNS = [
    "package", "partno", "codes", "lotno", "dcode", "Testdate", "shipdate",
    "boxno", "serialst", "serialsp", "inqty", "currqty", "testedqty", "goodqty", "yld", "이슈사항"
]

# 사용자 컬럼명 → 내부 표준 컬럼명 매핑
COLUMN_MAPPING = {
    "testdate": "Testdate",
    "shipdate": "shipdate",
    "codes": "codes",
    "serialst": "serialst",
    "serialsp": "serialsp"
}

@router.post("/generate_excel")
async def generate_excel(file: UploadFile = File(...)):
    try:
        # 1. 파일 읽기 (허용된 컬럼만)
        contents = await file.read()
        df = pd.read_excel(BytesIO(contents), usecols=lambda name: name in ALLOWED_COLUMNS)

        # 2. 컬럼명 소문자 → 표준명 변환
        df.columns = [col.strip().lower() for col in df.columns]
        df = df.rename(columns={col: COLUMN_MAPPING.get(col, col) for col in df.columns})

        # 날짜를 문자열로 변환
        for date_col in ["Testdate", "shipdate"]:
            if date_col in df.columns:
                df[date_col] = pd.to_datetime(df[date_col], errors="coerce") \
                    .dt.strftime("%Y-%m-%d")  # 문자열 변환

        # 4. 정렬
        sort_keys = [col for col in ["codes", "lotno", "Testdate", "shipdate", "serialst"] if col in df.columns]
        if sort_keys:
            df_sorted = df.sort_values(by=sort_keys, ascending=True, na_position="last")
        else:
            df_sorted = df

        # 5. 엑셀 파일로 저장
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_sorted.to_excel(writer, index=False, sheet_name="SortedData")
            apply_excel_formats(writer, df_sorted)  # 📌 숫자·퍼센트·날짜 서식 적용
        output.seek(0)

        # 6. 파일명 생성
        filename = f"sorted_serials_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        # 7. 다운로드 응답
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
