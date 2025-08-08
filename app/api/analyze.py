
from fastapi import APIRouter, UploadFile, File, Body
from fastapi.responses import JSONResponse
import pandas as pd
from io import BytesIO

router = APIRouter()

ALLOWED_COLUMNS = [
    "package", "partno", "codes", "lotno", "dcode", "Testdate", "shipdate",
    "boxno", "serialst", "serialsp", "inqty", "currqty", "testedqty", "goodqty", "yld", "이슈사항"
]

COLUMN_MAPPING = {
    "testdate": "Testdate",
    "shipdate": "shipdate",
    "codes": "codes",
    "serialst": "serialst",
    "serialsp": "serialsp"
}

def detect_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    duplicates = []
    for code, group in df.groupby("codes"):
        group = group.sort_values(by=["serialst"])
        for i in range(len(group) - 1):
            curr_end = group.iloc[i]["serialsp"]
            next_start = group.iloc[i + 1]["serialst"]
            if curr_end >= next_start:
                duplicates.append(group.iloc[i])
                duplicates.append(group.iloc[i + 1])
    return pd.DataFrame(duplicates).drop_duplicates() if duplicates else pd.DataFrame(columns=df.columns)

@router.post("/analyze_excel")
async def analyze_excel(
    file: UploadFile = File(...),
    filters: dict = Body(default={})
):
    try:
        contents = await file.read()
        df = pd.read_excel(BytesIO(contents), usecols=lambda name: name in ALLOWED_COLUMNS)

        # 컬럼 정리
        df.columns = [col.strip().lower() for col in df.columns]
        df = df.rename(columns={col: COLUMN_MAPPING.get(col, col) for col in df.columns})

        for date_col in ["Testdate", "shipdate"]:
            if date_col in df.columns:
                df[date_col] = pd.to_datetime(df[date_col], errors="coerce").dt.strftime("%Y-%m-%d")

        # 필터 적용
        df_filtered = df.copy()
        if "codes" in filters:
            df_filtered = df_filtered[df_filtered["codes"].isin(filters["codes"])]
        if "Testdate__gte" in filters:
            df_filtered = df_filtered[
                pd.to_datetime(df_filtered["Testdate"]) >= pd.to_datetime(filters["Testdate__gte"])
            ]

        # 정렬
        sort_keys = [col for col in ["codes", "lotno", "Testdate", "shipdate", "serialst"] if col in df.columns]
        if sort_keys:
            df_sorted = df_filtered.sort_values(by=sort_keys, ascending=True, na_position="last")
        else:
            df_sorted = df_filtered

        # 중복 체크
        df_duplicates = detect_duplicates(df_sorted)

        # 통계 생성
        stats = {
            "total_rows": len(df_filtered),
            "duplicate_rows": len(df_duplicates),
            "applied_filters": filters,
            "sort_keys": sort_keys
        }

        return JSONResponse(content={"status": "success", "stats": stats})

    except Exception as e:
        import traceback
        print("❌ analyze_excel 오류:", e)
        print(traceback.format_exc())
        return JSONResponse(status_code=500, content={"error": str(e)})
