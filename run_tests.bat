@echo off
cd /d %~dp0
call venv\Scripts\activate.bat
python -m pytest src/tests/test_app.py -v
pause 