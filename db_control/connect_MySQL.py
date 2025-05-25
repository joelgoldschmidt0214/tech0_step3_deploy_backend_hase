from sqlalchemy import create_engine

import os
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

# データベース接続情報
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_NAME = os.getenv('DB_NAME')

# MySQLのURL構築
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

SSL_CA_PATH = os.getenv('SSL_CA_PATH')
# エンジンの作成
engine = create_engine(
    DATABASE_URL,
    echo=True,
    pool_pre_ping=True,
    pool_recycle=3600,
    connect_args={
        # "ssl_ca": SSL_CA_PATH
        "ssl_verify_cert": True
    }
)

# --- 接続テスト (任意だが推奨) ---
def test_db_connection():
    try:
        with engine.connect() as connection: # 実際に接続を試みる
            print("Successfully connected to the database via SQLAlchemy engine!")
            print(f"Connected to: {engine.url}") # 接続先URLを再確認
    except Exception as e:
        print(f"Failed to connect to the database via SQLAlchemy engine: {e}")

if __name__ == "__main__": # このファイルが直接実行された場合にテスト
    test_db_connection()
else: # app.py などからインポートされた場合にテスト (任意)
    # アプリケーション起動時に一度だけ接続テストを行う場合
    # ただし、FastAPIの起動シーケンスによっては、ここでエラーになるとアプリが起動しない可能性も
    test_db_connection()
    # pass