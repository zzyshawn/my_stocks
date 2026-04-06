@echo off
cd /d "%~dp0"
echo Starting history data updater (full mode)...
python src/data/history/data_updater.py --full
pause