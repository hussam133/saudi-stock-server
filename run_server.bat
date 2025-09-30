@echo off
echo ================================
echo Saudi Stock Server - Local Run
echo ================================

REM التأكد إذا venv موجود
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

REM تفعيل venv
call venv\Scripts\activate

REM تحديث pip
python -m pip install --upgrade pip

REM تنزيل المكتبات
pip install -r requirements.txt

REM تشغيل السيرفر
python server.py
