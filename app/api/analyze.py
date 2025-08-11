from fastapi import APIRouter, UploadFile, File, Form, Body
from fastapi.responses import StreamingResponse, JSONResponse
import pandas as pd
from io import BytesIO, StringIO
from datetime import datetime
from app.utils.formatter import apply_excel_formats

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
    # Ensure serial columns are numeric
    df['serialst'] = pd.to_numeric(df.get('serialst', pd.Series()), errors='coerce')
    df['serialsp'] = pd.to_numeric(df.get('serialsp', pd.Series()), errors='coerce')
    duplicates = []
    for code, group in df.groupby("codes"):
        group = group.sort_values(by=["serialst"], na_position='last')
        for i in range(len(group) - 1):
            curr_end = group.iloc[i]["serialsp"]
            next_start = group.iloc[i + 1]["serialst"]
            if pd.notna(curr_end) and pd.notna(next_start) and curr_end >= next_start:
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
        df = pd.read_excel(BytesIO(contents), usecols=lambda c: c in ALLOWED_COLUMNS)

        # Column cleanup & mapping
        df.columns = [col.strip().lower() for col in df.columns]
        df = df.rename(columns={col: COLUMN_MAPPING.get(col, col) for col in df.columns})

        # Date formatting
        for date_col in ["Testdate", "shipdate"]:
            if date_col in df.columns:
                df[date_col] = pd.to_datetime(df[date_col], errors='coerce').dt.strftime("%Y-%m-%d")

        # Filtering
        df_filtered = df.copy()
        if "codes" in filters:
            df_filtered = df_filtered[df_filtered["codes"].isin(filters["codes"]) ]
        if "testdate__gte" in filters:
            df_filtered = df_filtered[
                pd.to_datetime(df_filtered["testdate"]) >= pd.to_datetime(filters["testdate__gte"]) ]

        # Sorting
        sort_keys = [k for k in ["codes", "lotno", "testdate", "shipdate", "serialst"] if k in df_filtered.columns]
        df_sorted = df_filtered.sort_values(by=sort_keys, ascending=True, na_position='last') if sort_keys else df_filtered

        # Duplicate detection
        df_dup = detect_duplicates(df_sorted)

        # Yield & defect stats
        stats = []
        for code, grp in df_dup.groupby("codes"):
            tested_total = int(grp.get("testedqty", pd.Series()).sum())
            good_total   = int(grp.get("goodqty", pd.Series()).sum())
            defect_count = tested_total - good_total
            yield_rate   = round((good_total / tested_total * 100) if tested_total else 0.0, 1)
            defect_rate  = round((defect_count / tested_total * 100) if tested_total else 0.0, 1)
            stats.append({
                "product_code": code,
                "testedqty":    tested_total,
                "goodqty":      good_total,
                "defect_count": defect_count,
                "yield_rate":   yield_rate,
                "defect_rate":  defect_rate
            })

        top_yield = max(stats, key=lambda x: x["yield_rate"], default=None)
        top_defect = max(stats, key=lambda x: x["defect_rate"], default=None)
        insights = []
        if top_yield:
            insights.append(f"가장 수율이 높은 제품은 {top_yield['product_code']} ({top_yield['yield_rate']}%)입니다.")
        if top_defect:
            insights.append(f"가장 불량율이 높은 제품은 {top_defect['product_code']} ({top_defect['defect_rate']}%)입니다.")
        insight = " ".join(insights)

        return JSONResponse(content={
            "status":      "success",
            "yield_stats": stats,
            "insight":     insight
        })

    except Exception as e:
        import traceback
        print("❌ analyze_excel 오류:", e)
        print(traceback.format_exc())
        return JSONResponse(status_code=500, content={"error": str(e)})

# File generation endpoint (alias for generate & download)
@router.post("/generate_excel")
@router.post("/download_result")
async def generate_excel(
    file: UploadFile = File(...),
    format: str = Form("xlsx"),
    filters: dict = Body(default={})
):
    try:
        contents = await file.read()
        df = pd.read_excel(BytesIO(contents), usecols=lambda name: name in ALLOWED_COLUMNS)

        df.columns = [col.strip().lower() for col in df.columns]
        df = df.rename(columns={col: COLUMN_MAPPING.get(col, col) for col in df.columns})

        for date_col in ["Testdate", "shipdate"]:
            if date_col in df.columns:
                df[date_col] = pd.to_datetime(df[date_col], errors='coerce').dt.strftime("%Y-%m-%d")

        df_filtered = df.copy()
        if "codes" in filters:
            df_filtered = df_filtered[df_filtered["codes"] .isin(filters["codes"])]
        if "Testdate__gte" in filters:
            df_filtered = df_filtered[
                pd.to_datetime(df_filtered["Testdate"]) >= pd.to_datetime(filters["Testdate__gte"])
            ]

        sort_keys = [col for col in ["codes", "lotno", "Testdate", "shipdate", "serialst"] if col in df.columns]
        df_sorted = df_filtered.sort_values(by=sort_keys, ascending=True, na_position="last") if sort_keys else df_filtered

        df_duplicates = detect_duplicates(df_sorted)

        if format == "csv":
            output = StringIO()
            df_sorted.to_csv(output, index=False, encoding="utf-8-sig")
            output.seek(0)
            filename = f"sheetflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            media_type = "text/csv"
        else:
            output = BytesIO()
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                df_sorted.to_excel(writer, index=False, sheet_name="SortedData")
                if not df_duplicates.empty:
                    df_duplicates.to_excel(writer, index=False, sheet_name="Duplicates")
                apply_excel_formats(writer, df_sorted)
            output.seek(0)
            filename = f"sheetflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

        return StreamingResponse(
            output,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except Exception as e:
        import traceback
        print("❌ generate_excel 오류:", e)
        print(traceback.format_exc())
        return JSONResponse(status_code=500, content={"error": str(e)})
