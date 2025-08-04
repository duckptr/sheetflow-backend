from fastapi import APIRouter, UploadFile, File
from fastapi.responses import StreamingResponse, JSONResponse
import pandas as pd
from io import BytesIO
from datetime import datetime

router = APIRouter()

COLUMN_MAPPING = {
    "codes": "제품코드",
    "testdate": "준비일",
    "shipdate": "출하일",
    "serialst": "시작시리얼",
    "serialsp": "종료시리얼",
}

@router.post("/")
async def export_excel(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        df = pd.read_excel(BytesIO(contents))
        df.columns = [col.lower() for col in df.columns]
        df = df.rename(columns={k: v for k, v in COLUMN_MAPPING.items() if k in df.columns})

        # 날짜 정리
        df["준비일"] = pd.to_datetime(df.get("준비일", pd.NaT), errors="coerce")
        df["출하일"] = pd.to_datetime(df.get("출하일", pd.NaT), errors="coerce")

        # 시리얼 존재 필터
        df = df[df["시작시리얼"].notnull() & df["종료시리얼"].notnull()]

        # 정렬된 전체 리스트 만들기
        rows = []
        for code, group in df.groupby("제품코드"):
            sorted_group = group.sort_values("출하일")
            for _, row in sorted_group.iterrows():
                rows.append({
                    "제품코드": code,
                    "준비일": row["준비일"].strftime("%Y-%m-%d") if pd.notnull(row["준비일"]) else None,
                    "출하일": row["출하일"].strftime("%Y-%m-%d") if pd.notnull(row["출하일"]) else None,
                    "시작시리얼": str(row["시작시리얼"]).strip(),
                    "종료시리얼": str(row["종료시리얼"]).strip(),
                })

        # DataFrame → Excel
        result_df = pd.DataFrame(rows)
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            result_df.to_excel(writer, index=False, sheet_name="GroupedSerials")

        output.seek(0)

        # 응답으로 파일 전송
        filename = f"grouped_serials_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
