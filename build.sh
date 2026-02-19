#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

# 收集靜態文件
python manage.py collectstatic --no-input

# 執行資料庫遷移
python manage.py makemigrationss
python manage.py migrate