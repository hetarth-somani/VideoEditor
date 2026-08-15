@echo off
echo [1/2] Activating Virtual Environment...
call venv\Scripts\activate

echo [2/2] Starting Video Editor Pro...
echo App will be available at http://localhost:5000
echo.
echo TIP: To stop the server, press Ctrl+C in this window.
echo.

:: Start Celery in a new window
start "Celery Worker" cmd /c "venv\Scripts\activate && start_celery.bat"

:: Start the Flask app
python app.py

pause
