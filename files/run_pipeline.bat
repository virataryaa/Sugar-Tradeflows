@echo off
cd /d "%~dp0"
set LOG=%~dp0run_log.txt
set EMAIL=virat.arya@etgworld.com
set FAILED=0
set GIT_STATUS=skipped

:: Prevent Git Credential Manager from showing an interactive dialog in unattended runs.
:: If credentials are cached it pushes silently; if not, it fails immediately instead of hanging.
set GCM_INTERACTIVE=never
set GIT_TERMINAL_PROMPT=0

echo. >> "%LOG%"
echo ============================================================ >> "%LOG%"
echo Sugar TDM Pipeline  --  %DATE% %TIME% >> "%LOG%"
echo ============================================================ >> "%LOG%"

C:\Users\virat.arya\AppData\Local\anaconda3\python.exe sugar_exports_ingest.py >> "%LOG%" 2>&1
if errorlevel 1 (
    echo [ERROR] sugar_exports_ingest.py failed >> "%LOG%"
    set FAILED=1
    goto :send_mail
)

C:\Users\virat.arya\AppData\Local\anaconda3\python.exe sugar_imports_ingest.py >> "%LOG%" 2>&1
if errorlevel 1 (
    echo [ERROR] sugar_imports_ingest.py failed >> "%LOG%"
    set FAILED=1
    goto :send_mail
)

C:\Users\virat.arya\AppData\Local\anaconda3\python.exe sugar_imports_eu_ingest.py >> "%LOG%" 2>&1
if errorlevel 1 (
    echo [ERROR] sugar_imports_eu_ingest.py failed >> "%LOG%"
    set FAILED=1
    goto :send_mail
)

C:\Users\virat.arya\AppData\Local\anaconda3\python.exe sugar_exports_eu_ingest.py >> "%LOG%" 2>&1
if errorlevel 1 (
    echo [ERROR] sugar_exports_eu_ingest.py failed >> "%LOG%"
    set FAILED=1
    goto :send_mail
)

echo Pushing to GitHub... >> "%LOG%"
git add data\tdm_sugar_exports.parquet data\tdm_sugar_exports_eu.parquet data\tdm_sugar_imports.parquet data\tdm_sugar_imports_eu.parquet >> "%LOG%" 2>&1
git commit -m "auto: update sugar parquets %DATE% %TIME%" >> "%LOG%" 2>&1
git push >> "%LOG%" 2>&1
if errorlevel 1 (
    echo [ERROR] git push failed >> "%LOG%"
    set GIT_STATUS=failed
    set FAILED=1
) else (
    echo [OK] git push succeeded >> "%LOG%"
    set GIT_STATUS=pushed
)

:send_mail
echo All done -- %DATE% %TIME% >> "%LOG%"
echo ============================================================ >> "%LOG%"

if %FAILED%==0 (
    C:\Users\virat.arya\AppData\Local\anaconda3\python.exe notify.py ok %GIT_STATUS%
) else (
    C:\Users\virat.arya\AppData\Local\anaconda3\python.exe notify.py failed %GIT_STATUS%
)
