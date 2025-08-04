import os
import pandas as pd
from fastapi import UploadFile

UPLOAD_DIR = "uploaded_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)

async def save_uploaded_file(file: UploadFile) -> str:
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    return file_path

def analyze_duplicates(file_path: str, subset: list[str] = None) -> dict:
    df = pd.read_excel(file_path)

    if subset:
        duplicated = df[df.duplicated(subset=subset, keep=False)]
    else:
        duplicated = df[df.duplicated(keep=False)]

    return {
        "total_rows": len(df),
        "duplicated_rows": len(duplicated),
        "preview": duplicated.head(10).to_dict(orient="records")
    }
