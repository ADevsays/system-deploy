FROM node:22-bookworm-slim AS node_runtime

FROM python:3.11-slim

WORKDIR /app

# yt-dlp supports Node 20+. Copying Node 22 avoids the large toolchain
# required to add a third-party APT repository during every image build.
COPY --from=node_runtime /usr/local/bin/node /usr/local/bin/node

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    fontconfig \
    wget \
    libstdc++6 \
    && node --version \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app ./app
COPY grok_system_prompt.txt /app/grok_system_prompt.txt
COPY template_script_prompt.txt /app/template_script_prompt.txt
COPY llms.txt /app/llms.txt

RUN mkdir -p /app/app/assets/fonts && \
    wget -q "https://raw.githubusercontent.com/google/fonts/main/ofl/poppins/Poppins-Regular.ttf" -O /app/app/assets/fonts/Poppins-Regular.ttf && \
    wget -q "https://raw.githubusercontent.com/google/fonts/main/ofl/poppins/Poppins-Bold.ttf" -O /app/app/assets/fonts/Poppins-Bold.ttf && \
    wget -q "https://raw.githubusercontent.com/google/fonts/main/ofl/poppins/Poppins-Medium.ttf" -O /app/app/assets/fonts/Poppins-Medium.ttf && \
    wget -q "https://raw.githubusercontent.com/google/fonts/main/ofl/poppins/Poppins-SemiBold.ttf" -O /app/app/assets/fonts/Poppins-SemiBold.ttf && \
    fc-cache -fv && \
    echo '<?xml version="1.0"?><!DOCTYPE fontconfig SYSTEM "fonts.dtd"><fontconfig><match target="pattern"><edit name="dpi" mode="assign"><double>96</double></edit></match></fontconfig>' > /etc/fonts/local.conf

RUN mkdir -p /app/temp

ENV PYTHONUNBUFFERED=1
ENV YOUTUBE_JS_RUNTIME=node

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
