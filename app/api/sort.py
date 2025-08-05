from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse
import pandas as pd
from io import BytesIO
from app.utils.cleaner import clean_dataframe
from app.utils.formatter import format_numbers_preview

router = APIRouter()

@router.post("/sort_excel")
async def sort_excel(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        allowed_columns = [
            "package", "partno", "codes", "lotno", "dcode", "Testdate", "shipdate",
            "boxno", "serialst", "serialsp", "inqty", "currqty", "testedqty", "goodqty", "yld"
        ]
        df = pd.read_excel(BytesIO(contents), usecols=lambda name: name in allowed_columns)

        original_columns = df.columns.tolist()

        df_lower = df.copy()
        df_lower.columns = [col.lower() for col in df_lower.columns]
        rename_map = {
            "testdate": "Testdate",
            "shipdate": "shipdate",
            "codes": "codes",
            "serialst": "serialst",
            "serialsp": "serialsp"
        }
        df_lower = df_lower.rename(columns={col: rename_map.get(col, col) for col in df_lower.columns})

        for date_col in ["Testdate", "shipdate"]:
            if date_col in df_lower.columns:
                df_lower[date_col] = pd.to_datetime(df_lower[date_col], errors="coerce")

        sort_keys = [col for col in ["codes", "lotno", "Testdate", "shipdate", "serialst"] if col in df_lower.columns]
        df_sorted = df_lower.sort_values(by=sort_keys, ascending=True, na_position="last") if sort_keys else df_lower

        df_sorted = df_sorted[[col for col in original_columns if col in df_sorted.columns]]
        df_sorted = clean_dataframe(df_sorted)

        for date_col in ["Testdate", "shipdate"]:
            if date_col in df_sorted.columns:
                df_sorted[date_col] = df_sorted[date_col].apply(
                    lambda x: x.strftime("%Y-%m-%d") if pd.notnull(x) and hasattr(x, "strftime") else x
                )

        rows = [format_numbers_preview(r) for r in df_sorted.head(50).to_dict(orient="records")]
        return {"sorted_preview": rows}

    except Exception as e:
        print("❌ sort_excel 오류:", e)
        return JSONResponse(status_code=500, content={"error": str(e)})
