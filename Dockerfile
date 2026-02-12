FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    ffmpeg \
    fontconfig \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /usr/share/fonts/poppins && \
    wget -q "https://raw.githubusercontent.com/google/fonts/main/ofl/poppins/Poppins-Regular.ttf" -O /usr/share/fonts/poppins/Poppins-Regular.ttf && \
    wget -q "https://raw.githubusercontent.com/google/fonts/main/ofl/poppins/Poppins-Bold.ttf" -O /usr/share/fonts/poppins/Poppins-Bold.ttf && \
    wget -q "https://raw.githubusercontent.com/google/fonts/main/ofl/poppins/Poppins-Medium.ttf" -O /usr/share/fonts/poppins/Poppins-Medium.ttf && \
    wget -q "https://raw.githubusercontent.com/google/fonts/main/ofl/poppins/Poppins-SemiBold.ttf" -O /usr/share/fonts/poppins/Poppins-SemiBold.ttf && \
    fc-cache -fv

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app ./app

RUN mkdir -p /app/temp

ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
