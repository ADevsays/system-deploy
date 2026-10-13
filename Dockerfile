FROM python:3.11-slim

WORKDIR /app

# yt-dlp requires Node 20+ for YouTube's JavaScript challenges.
# NodeSource supplies Node 22; Debian's default package is Node 18.
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    gnupg \
    ffmpeg \
    fontconfig \
    wget \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_22.x nodistro main" > /etc/apt/sources.list.d/nodesource.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends nodejs \
    && node --version \
    && apt-get purge -y --auto-remove curl gnupg \
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
