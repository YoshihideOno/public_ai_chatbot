# ベースイメージとしてNode.jsのLTSバージョンを使用
FROM node:20-alpine

# 作業ディレクトリを設定
WORKDIR /app

# package.jsonとpackage-lock.jsonをコピー
COPY package*.json ./

# 依存関係をインストール
RUN npm install

# アプリケーションのソースコードをコピー
COPY . .

# 開発環境ではビルドをスキップしてdevサーバーを起動
CMD ["npm", "run", "dev"]
