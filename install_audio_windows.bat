@echo off
cd /d "%~dp0"
call venv311\Scripts\activate
python -m pip install -r requirements-audio.txt
pause
