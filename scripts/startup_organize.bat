@echo off
REM Wait 60 seconds for Ollama and agent to start first
timeout /t 60 /nobreak >nul

REM Run the file organizer
cd /d C:\Users\97150\macal_pc
call .venv\Scripts\activate.bat
python scripts/organize_downloads.py

REM Send Telegram notification
curl -s "https://api.telegram.org/bot8621184851:AAEgCGHMGYpWQtDevwdm2kHt6OF3sZdlVkQ/sendMessage?chat_id=8355378781&text=PC+started.+Downloads+organized."
