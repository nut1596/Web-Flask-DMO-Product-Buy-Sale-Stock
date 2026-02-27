# ใช้ Python base image
FROM python:3.11-slim

# กำหนด working directory
WORKDIR /app

# copy ไฟล์ requirements ก่อน (cache layer)
COPY requirements.txt .

# ติดตั้ง dependencies
RUN pip install --no-cache-dir -r requirements.txt

# copy ทั้งโปรเจคเข้า container
COPY . .

# เปิด port
EXPOSE 5000

# รันด้วย Gunicorn (Production)
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]