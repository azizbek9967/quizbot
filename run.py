import subprocess
import sys
import os
import time
from dotenv import load_dotenv

load_dotenv()

def main():
    port = int(os.environ.get("PORT", 8000))
    os.environ.setdefault("DATABASE_URL", "sqlite:///./app.db")
    os.environ.setdefault("API_URL", f"http://127.0.0.1:{port}")
    
    # Initialize database tables and seed sample data
    print("🌱 Initializing database and running seed...")
    try:
        import seed
        seed.main()
    except Exception as e:
        print(f"⚠️ Database seed warning: {e}")

    uvicorn_cmd = [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", str(port)]
    bot_cmd = [sys.executable, "bot.py"]
    
    print(f"🚀 Starting FastAPI backend on port {port} and Telegram bot concurrently...")
    api_process = subprocess.Popen(uvicorn_cmd)
    time.sleep(2.0)
    bot_process = subprocess.Popen(bot_cmd)
    
    try:
        api_process.wait()
        bot_process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Stopping services...")
        api_process.terminate()
        bot_process.terminate()
        api_process.wait()
        bot_process.wait()
        print("✅ Stopped.")

if __name__ == "__main__":
    main()
