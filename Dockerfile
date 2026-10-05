# Usa uma imagem oficial do Python baseada em Debian (ótima para o Playwright)
FROM python:3.11-slim

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Instala dependências de sistema necessárias para o Playwright e Chromium rodarem no Linux
RUN apt-get update && apt-get install -y \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libexpat1 \
    libfontconfig1 \
    libgbm1 \
    libglib2.0-0 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libstdc++6 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libxrender1 \
    libxss1 \
    libxtst6 \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copia e instala as dependências do Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Instala os binários do navegador Playwright (Chromium)
RUN playwright install chromium

# Copia o restante do código do projeto para dentro do container
COPY . .

# Expõe a porta padrão que o Streamlit utiliza
EXPOSE 10000

# Comando para iniciar o aplicativo Streamlit no Render
CMD ["streamlit", "run", "app.py", "--server.port=10000", "--server.address=0.0.0.0"]