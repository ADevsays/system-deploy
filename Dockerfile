FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    ffmpeg \
    fontconfig \
    wget \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app ./app

RUN mkdir -p /app/app/assets/fonts && \
    wget -q "https://raw.githubusercontent.com/google/fonts/main/ofl/poppins/Poppins-Regular.ttf" -O /app/app/assets/fonts/Poppins-Regular.ttf && \
    wget -q "https://raw.githubusercontent.com/google/fonts/main/ofl/poppins/Poppins-Bold.ttf" -O /app/app/assets/fonts/Poppins-Bold.ttf && \
    wget -q "https://raw.githubusercontent.com/google/fonts/main/ofl/poppins/Poppins-Medium.ttf" -O /app/app/assets/fonts/Poppins-Medium.ttf && \
    wget -q "https://raw.githubusercontent.com/google/fonts/main/ofl/poppins/Poppins-SemiBold.ttf" -O /app/app/assets/fonts/Poppins-SemiBold.ttf && \
    fc-cache -fv && \
    echo '<?xml version="1.0"?><!DOCTYPE fontconfig SYSTEM "fonts.dtd"><fontconfig><match target="pattern"><edit name="dpi" mode="assign"><double>96</double></edit></match></fontconfig>' > /etc/fonts/local.conf

RUN mkdir -p /app/temp

ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
