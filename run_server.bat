@echo off
echo ==============================
echo Saudi Stock Server - Local Run
echo ==============================

REM الانتقال لمجلد المشروع
cd /d "%~dp0saudi-stock-server"

REM التحقق من وجود venv، إذا مش موجود يعمل واحد
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

REM تفعيل venv
call venv\Scripts\activate

REM تحديث pip
python -m pip install --upgrade pip

REM تنزيل المتطلبات
pip install -r requirements.txt

REM تشغيل السيرفر
python server.py

pause
