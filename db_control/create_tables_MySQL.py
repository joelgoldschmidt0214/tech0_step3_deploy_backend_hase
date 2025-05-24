import os
from pathlib import Path
from sqlalchemy import inspect, Table, MetaData
from sqlalchemy.orm import sessionmaker
from datetime import datetime # datetime をインポート
import uuid # uuid をインポート

# MySQL用のモデルとエンジンをインポート
from db_control.mymodels_MySQL import Base, Customers, Items, Purchases, PurchaseDetails
from db_control.connect_MySQL import engine # connect_MySQL.py にMySQL接続設定があると想定

def drop_all_known_tables(current_engine, metadata_obj: MetaData):
    """
    metadata_obj に登録されている全てのテーブルを削除します。
    外部キー制約を考慮し、drop_all を使用します。
    """
    print("Attempting to drop all known tables (if they exist)...")
    try:
        # metadata.drop_all は依存関係を考慮してテーブルを削除してくれる
        metadata_obj.drop_all(bind=current_engine, checkfirst=True)
        print("All known tables dropped successfully (or did not exist).")
    except Exception as e:
        print(f"Error dropping tables: {e}")
        # 実際の運用では、ここでエラーをraiseするか、より詳細なログを残す
        # raise

def create_all_tables(current_engine, metadata_obj: MetaData):
    """
    metadata_obj に登録されている全てのテーブルを作成します。
    """
    print("Creating all tables defined in metadata...")
    try:
        metadata_obj.create_all(bind=current_engine)
        print("All tables created successfully!")
    except Exception as e:
        print(f"Error creating tables: {e}")
        raise

def insert_sample_data():
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        print("Inserting sample data...")

        # --- Customers ---
        customer1_uuid = uuid.uuid4()
        customer2_uuid = uuid.uuid4()
        sample_customers = [
            Customers(internal_id=customer1_uuid, customer_id="C0001", customer_name="山田 太郎", age=35, gender="男性"),
            Customers(internal_id=customer2_uuid, customer_id="C0002", customer_name="佐藤 花子", age=28, gender="女性"),
        ]
        # 既存チェック (customer_id がユニークなため)
        for cust_data in sample_customers:
            existing = session.query(Customers).filter_by(customer_id=cust_data.customer_id).first()
            if not existing:
                session.add(cust_data)
            else:
                print(f"Customer with customer_id {cust_data.customer_id} already exists. Skipping.")
        session.flush() # IDを確定させるため (特にUUID参照する場合)

        # --- Items ---
        sample_items = [
            Items(item_id="ITEM001", item_name="高性能ラップトップ", price=150000),
            Items(item_id="ITEM002", item_name="ワイヤレスマウス", price=3500),
            Items(item_id="ITEM003", item_name="メカニカルキーボード", price=8000),
        ]
        for item_data in sample_items:
            existing = session.query(Items).filter_by(item_id=item_data.item_id).first()
            if not existing:
                session.add(item_data)
            else:
                print(f"Item with item_id {item_data.item_id} already exists. Skipping.")
        session.flush()

        # --- Purchases ---
        # customer1_uuid を使うために、上記で customer1 が追加されている必要がある
        # または、事前にDBに存在する顧客の internal_id を使う
        customer_for_purchase1 = session.query(Customers).filter_by(customer_id="C0001").first()
        customer_for_purchase2 = session.query(Customers).filter_by(customer_id="C0002").first()

        if customer_for_purchase1 and customer_for_purchase2:
            purchase1 = Purchases(customer_internal_id=customer_for_purchase1.internal_id, purchase_date=datetime(2023, 10, 26, 10, 30, 0))
            purchase2 = Purchases(customer_internal_id=customer_for_purchase2.internal_id, purchase_date=datetime(2023, 10, 27, 14, 15, 0))
            session.add_all([purchase1, purchase2])
            session.flush() # purchase_id を確定させるため

            # --- PurchaseDetails ---
            # purchase1 と purchase2 の id が確定している必要がある
            item1 = session.query(Items).filter_by(item_id="ITEM001").first()
            item2 = session.query(Items).filter_by(item_id="ITEM002").first()
            item3 = session.query(Items).filter_by(item_id="ITEM003").first()

            if item1 and item2 and item3:
                details = [
                    PurchaseDetails(purchase_id=purchase1.purchase_id, item_id=item1.item_id, quantity=1),
                    PurchaseDetails(purchase_id=purchase1.purchase_id, item_id=item2.item_id, quantity=1),
                    PurchaseDetails(purchase_id=purchase2.purchase_id, item_id=item3.item_id, quantity=2),
                    PurchaseDetails(purchase_id=purchase2.purchase_id, item_id=item2.item_id, quantity=1),
                ]
                session.add_all(details)
        else:
            print("Skipping Purchases and PurchaseDetails due to missing customer data for sample.")


        session.commit()
        print("Sample data inserted (or skipped if existing) successfully!")

        # (任意) 挿入データの確認
        print("\n--- Inserted Customers (MySQL) ---")
        for customer_obj in session.query(Customers).limit(5).all(): # 全件表示は量が多い場合があるのでlimit
            print(f"Internal ID: {customer_obj.internal_id}, Customer ID: {customer_obj.customer_id}, Name: {customer_obj.customer_name}")
        # 他のテーブルも同様に確認可能

    except Exception as e:
        print(f"Error inserting sample data: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    print(f"Using database engine for MySQL: {engine.url}")
    
    # 1. 既存の関連テーブルを全て削除 (外部キー制約のため)
    drop_all_known_tables(engine, Base.metadata)
    
    # 2. 新しいスキーマで全てのテーブルを作成
    create_all_tables(engine, Base.metadata)
    
    # 3. サンプルデータを挿入
    insert_sample_data()