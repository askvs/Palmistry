@echo off
rem MysticLens backend dev server (no --reload; restart manually after backend code changes)
rem Logs append to backend_dev_server.log in the workspace root.
cd /d "C:\Users\ASUS\Desktop\Palmistry"
"C:\Users\ASUS\Desktop\Palmistry\.venv\Scripts\python.exe" -m uvicorn app.main:app --app-dir backend --port 8000 >> "C:\Users\ASUS\Desktop\Palmistry\backend_dev_server.log" 2>&1
