import uvicorn
import webbrowser
import threading
import time
import sys
import os

# 🔹 PyInstaller 빌드 시 FastAPI 하위 모듈 누락 방지
import fastapi.middleware.cors
import fastapi.responses

def open_browser():
    # Flutter 웹뷰 사용할 경우 브라우저는 열 필요 없음
    pass

if __name__ == "__main__":
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, base_dir)

    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
        log_config=None
    )
