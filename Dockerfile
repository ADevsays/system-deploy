FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    ffmpeg \
    fontconfig \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /usr/share/fonts/poppins && \
    wget -q "https://fonts.google.com/download?family=Poppins" -O /tmp/poppins.zip && \
    unzip -o /tmp/poppins.zip -d /usr/share/fonts/poppins && \
    rm /tmp/poppins.zip && \
    fc-cache -fv

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app ./app

RUN mkdir -p /app/temp

ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
