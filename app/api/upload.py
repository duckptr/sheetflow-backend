from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse
import pandas as pd
import os, math
from app.utils.cleaner import clean_dataframe
from app.utils.formatter import format_numbers_preview

router = APIRouter()

UPLOAD_DIR = "uploaded_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)

latest_result = None

def clean_json_safe(obj):
    if isinstance(obj, float) and math.isnan(obj):
        return None
    if isinstance(obj, list):
        return [clean_json_safe(x) for x in obj]
    if isinstance(obj, dict):
        return {k: clean_json_safe(v) for k, v in obj.items()}
    return obj

@router.post("/")
async def upload_excel(file: UploadFile = File(...)):
    global latest_result
    try:
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())

        allowed_columns = [
            "package", "partno", "codes", "lotno", "dcode", "Testdate", "shipdate",
            "boxno", "serialst", "serialsp", "inqty", "currqty", "testedqty", "goodqty", "yld"
        ]
        df = pd.read_excel(file_path, usecols=lambda name: name in allowed_columns)

        df.columns = [col.strip().lower() for col in df.columns]
        rename_map = {
            "testdate": "Testdate",
            "shipdate": "shipdate",
            "codes": "codes",
            "serialst": "serialst",
            "serialsp": "serialsp"
        }
        df = df.rename(columns={col: rename_map.get(col, col) for col in df.columns})

        for date_col in ["Testdate", "shipdate"]:
            if date_col in df.columns:
                df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
                df[date_col] = df[date_col].apply(lambda x: x.strftime("%Y-%m-%d") if pd.notnull(x) else None)

        required = {"codes", "serialst", "serialsp"}
        if not required.issubset(df.columns):
            return JSONResponse(status_code=400, content={"error": "❌ Missing required columns"})

        dups = df[df.duplicated(subset=["codes", "serialst", "serialsp", "Testdate"], keep=False)].copy()

        for date_col in ["Testdate", "shipdate"]:
            if date_col in dups.columns:
                dups[date_col] = pd.to_datetime(dups[date_col], errors="coerce")
                dups[date_col] = dups[date_col].apply(lambda x: x.strftime("%Y-%m-%d") if pd.notnull(x) else None)

        df = clean_dataframe(df)
        dups = clean_dataframe(dups)

        safe_result = {
            "total": len(df),
            "duplicated": len(dups),
            "duplicates": [format_numbers_preview(r) for r in dups.to_dict(orient="records")]
        }
        safe_result = clean_json_safe(safe_result)

        latest_result = safe_result
        return JSONResponse(content={"result": safe_result})

    except Exception as e:
        print("❌ 예외 발생:", e)
        return JSONResponse(status_code=500, content={"error": str(e)})
