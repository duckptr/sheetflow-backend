
import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from threading import Thread
import pandas as pd
from io import BytesIO
from datetime import datetime

WATCH_DIR = "uploaded_files"  # 감시할 폴더
OUTPUT_DIR = "auto_generated"  # 결과 저장 폴더
os.makedirs(OUTPUT_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = [".xlsx", ".xls", ".csv"]

class ExcelHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return

        _, ext = os.path.splitext(event.src_path)
        if ext.lower() not in ALLOWED_EXTENSIONS:
            return

        print(f"📁 새 파일 감지됨: {event.src_path}")
        try:
            if ext.lower() == ".csv":
                df = pd.read_csv(event.src_path)
            else:
                df = pd.read_excel(event.src_path)

            # 기본 정렬 (예시)
            sort_keys = [col for col in ["codes", "lotno", "Testdate", "shipdate", "serialst"] if col in df.columns]
            df_sorted = df.sort_values(by=sort_keys) if sort_keys else df

            # 자동 저장
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            out_path = os.path.join(OUTPUT_DIR, f"autogen_{timestamp}.xlsx")
            df_sorted.to_excel(out_path, index=False)
            print(f"✅ 자동 저장됨: {out_path}")

        except Exception as e:
            print("❌ 자동 분석 중 오류 발생:", e)

def start_watchdog():
    event_handler = ExcelHandler()
    observer = Observer()
    observer.schedule(event_handler, WATCH_DIR, recursive=False)
    observer_thread = Thread(target=observer.start, daemon=True)
    observer_thread.start()
    print(f"🔍 폴더 감시 시작됨: {WATCH_DIR}")
