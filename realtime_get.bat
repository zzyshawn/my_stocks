@echo off
cd /d "%~dp0"
echo Starting realtime data fetcher (normal mode)...
python src/data/realtime/my_real_time.py
pause