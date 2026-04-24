@echo off
cd /d "%~dp0"
set LOG=%~dp0run_log.txt
set EMAIL=virat.arya@etgworld.com
set FAILED=0

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

echo Pushing to GitHub... >> "%LOG%"
git add data\tdm_sugar_exports.parquet data\tdm_sugar_imports.parquet data\tdm_sugar_imports_eu.parquet >> "%LOG%" 2>&1
git commit -m "auto: update sugar parquets %DATE% %TIME%" >> "%LOG%" 2>&1
git push >> "%LOG%" 2>&1
if errorlevel 1 (
    echo [ERROR] git push failed >> "%LOG%"
    set FAILED=1
) else (
    echo [OK] git push succeeded >> "%LOG%"
)

:send_mail
echo All done -- %DATE% %TIME% >> "%LOG%"
echo ============================================================ >> "%LOG%"

if %FAILED%==0 (
    powershell -NoProfile -Command "$o = New-Object -ComObject Outlook.Application; $m = $o.CreateItem(0); $m.To = '%EMAIL%'; $m.Subject = 'Sugar TDM Pipeline - OK [%DATE%]'; $m.Body = 'Sugar TDM pipeline completed successfully on %DATE% at %TIME%.'; $m.Send()"
) else (
    powershell -NoProfile -Command "$o = New-Object -ComObject Outlook.Application; $m = $o.CreateItem(0); $m.To = '%EMAIL%'; $m.Subject = 'Sugar TDM Pipeline - FAILED [%DATE%]'; $m.Body = 'Sugar TDM pipeline failed on %DATE% at %TIME%.`nCheck log: %LOG%'; $m.Send()"
)
