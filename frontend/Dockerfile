# ベースイメージとしてNode.jsのLTSバージョンを使用（Debianベース）
FROM node:20-slim

# Playwrightのブラウザを実行するために必要な依存関係をインストール
# Debian/UbuntuでPlaywrightを実行するために必要な依存関係
RUN apt-get update && apt-get install -y \
    chromium \
    libnss3 \
    libfreetype6 \
    libharfbuzz0b \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    libxrender1 \
    libxshmfence1 \
    libxss1 \
    libxtst6 \
    libu2f-udev \
    libvulkan1 \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Playwrightの環境変数を設定
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
# Debian/UbuntuではPlaywrightのブラウザをダウンロードして使用

# 作業ディレクトリを設定
WORKDIR /app

# package.jsonとpackage-lock.jsonをコピー
COPY package*.json ./

# 依存関係をインストール
RUN npm install

# Playwrightのブラウザをインストール（Alpine Linux対応）
RUN npx playwright install chromium

# アプリケーションのソースコードをコピー
COPY . .

# 開発環境ではビルドをスキップしてdevサーバーを起動
CMD ["npm", "run", "dev"]
