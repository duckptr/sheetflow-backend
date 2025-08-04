from fastapi import APIRouter
from app.api.upload import latest_result  # ✅ 정확한 경로로 import

router = APIRouter()

@router.get("/")
async def get_result():
    if latest_result is None:
        return {
            "result": {
                "total": 0,
                "duplicated": 0,
                "duplicates": []
            }
        }
    return {"result": latest_result}
