@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Starting Final CI Review on http://localhost:8765 ...
start "" "http://localhost:8765/Final-CI-Review.html"
python -m http.server 8765
