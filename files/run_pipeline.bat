@echo off
cd /d "%~dp0"
echo ============================================================
echo Sugar TDM Pipeline  --  %DATE% %TIME%
echo ============================================================

C:\Users\virat.arya\AppData\Local\anaconda3\python.exe sugar_exports_ingest.py
if errorlevel 1 ( echo [ERROR] sugar_exports_ingest.py failed & exit /b 1 )

C:\Users\virat.arya\AppData\Local\anaconda3\python.exe sugar_imports_ingest.py
if errorlevel 1 ( echo [ERROR] sugar_imports_ingest.py failed & exit /b 1 )

C:\Users\virat.arya\AppData\Local\anaconda3\python.exe sugar_imports_eu_ingest.py
if errorlevel 1 ( echo [ERROR] sugar_imports_eu_ingest.py failed & exit /b 1 )

echo ============================================================
echo All done.
echo ============================================================
