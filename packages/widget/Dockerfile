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

# ビルドとサーバー起動はdocker-compose.ymlのcommandで実行
# 開発環境ではボリュームマウントでホットリロード可能

