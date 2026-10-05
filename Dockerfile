FROM python:3.11-slim

# Cria um utilizador não-root exigido pelo Hugging Face
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

WORKDIR /app

# Instala dependências do sistema necessárias para o Playwright (como root temporariamente)
USER root
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

# Retorna para o utilizador padrão
USER user

# Copia e instala as dependências do Python
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Instala os binários do Chromium para o Playwright
RUN playwright install chromium

# Copia os arquivos do projeto
COPY --chown=user . .

# Porta padrão exigida pelo Hugging Face Spaces
EXPOSE 7860

CMD ["streamlit", "run", "app.py", "--server.port=7860", "--server.address=0.0.0.0"]