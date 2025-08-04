from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse
import pandas as pd
import os

router = APIRouter()

UPLOAD_DIR = "uploaded_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)

latest_result = None  # 최근 분석 결과 저장용

# 사용자 컬럼명을 내부 분석용 컬럼명으로 매핑
COLUMN_MAPPING = {
    "codes": "제품코드",
    "testdate": "날짜",
    "shipdate": "날짜",  # 둘 다 있을 경우 shipdate 우선
    "serialst": "시작시리얼",
    "serialsp": "종료시리얼",
}


@router.post("/")
async def upload_excel(file: UploadFile = File(...)):
    global latest_result

    try:
        print("📥 upload_excel 함수 진입!")  # 디버깅용 로그

        # 1. 파일 저장
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        print(f"📄 파일 저장 완료: {file.filename}")

        # 2. 엑셀 읽기
        df = pd.read_excel(file_path)
        print(f"📊 원본 데이터: {len(df)} rows")

        # 3. 컬럼명 전처리 및 매핑
        df.columns = [col.strip().lower() for col in df.columns]
        df = df.rename(columns={col: COLUMN_MAPPING.get(col, col) for col in df.columns})

        # 4. 날짜 컬럼 우선순위 처리
        if "shipdate" in df.columns:
            df["날짜"] = df["shipdate"]
        elif "testdate" in df.columns:
            df["날짜"] = df["testdate"]

        # 5. 필수 컬럼 확인
        required = {"제품코드", "시작시리얼", "종료시리얼", "날짜"}
        if not required.issubset(set(df.columns)):
            missing = required - set(df.columns)
            return JSONResponse(status_code=400, content={"error": f"❌ 누락된 컬럼: {missing}"})

        # 6. 중복 항목 추출
        dups = df[df.duplicated(subset=["제품코드", "시작시리얼", "종료시리얼", "날짜"], keep=False)]

        print(f"🟡 중복 항목 수: {len(dups)}")

        # ✅ 6.5. datetime을 문자열로 변환 (JSON 오류 방지)
        dups["날짜"] = dups["날짜"].astype(str)

        # 7. NaN 처리 후 결과 구성
        safe_result = {
            "total": len(df),
            "duplicated": len(dups),
            "duplicates": dups.fillna("").to_dict(orient="records"),
        }

        latest_result = safe_result
        return JSONResponse(content={"result": safe_result})

    except Exception as e:
        print("❌ 예외 발생:", e)
        return JSONResponse(status_code=500, content={"error": str(e)})
