# uname() error回避
import platform
print("platform", platform.uname())


from sqlalchemy import create_engine, insert, delete, update, select
import sqlalchemy
from sqlalchemy.orm import sessionmaker
import json
import pandas as pd
from db_control.connect_MySQL import engine
from db_control.mymodels_MySQL import Customers
from uuid import UUID


def myinsert(mymodel, values):
    # session構築
    Session = sessionmaker(bind=engine)
    session = Session()

    query = insert(mymodel).values(values)
    try:
        # トランザクションを開始
        with session.begin():
            # データの挿入
            result = session.execute(query)
    except sqlalchemy.exc.IntegrityError:
        print("一意制約違反により、挿入に失敗しました")
        session.rollback()

    # セッションを閉じる
    session.close()
    return "inserted"

def myinsert_orm(mymodel, values: dict): # values は Pydantic モデルの dict
    with Session(engine) as session:
        try:
            # internal_id はモデル定義の default=uuid.uuid4 で自動生成されるので、values には不要
            db_item = mymodel(**values)
            session.add(db_item)
            session.commit()
            session.refresh(db_item) # DBから最新の状態（生成されたinternal_idなど）を読み込む
            return db_item # ORMオブジェクトを返す
        except sqlalchemy.exc.IntegrityError as e:
            print(f"IntegrityError during insert: {e}")
            session.rollback()
            return None
        except Exception as e:
            print(f"Error in myinsert_orm: {e}")
            session.rollback()
            return None

def myselect(mymodel, customer_id):
    # session構築
    Session = sessionmaker(bind=engine)
    session = Session()
    query = session.query(mymodel).filter(mymodel.customer_id == customer_id)
    try:
        # トランザクションを開始
        with session.begin():
            result = query.all()
        # 結果をオブジェクトから辞書に変換し、リストに追加
        result_dict_list = []
        for customer_info in result:
            result_dict_list.append({
                "customer_id": customer_info.customer_id,
                "customer_name": customer_info.customer_name,
                "age": customer_info.age,
                "gender": customer_info.gender
            })
        # リストをJSONに変換
        result_json = json.dumps(result_dict_list, ensure_ascii=False)
    except sqlalchemy.exc.IntegrityError:
        print("一意制約違反により、挿入に失敗しました")

    # セッションを閉じる
    session.close()
    return result_json

def myselect_by_internal_id(mymodel, internal_id: UUID): # 引数を UUID 型に
    with Session(engine) as session:
        # internal_id で検索
        result = session.get(mymodel, internal_id) #主キーでの検索は session.get が効率的
        # result = session.scalars(select(mymodel).filter_by(internal_id=internal_id)).first() # filter_by も使える
        return result # ORMオブジェクトまたはNoneを返す

# def myselectAll(mymodel):
#     # session構築
#     Session = sessionmaker(bind=engine)
#     session = Session()
#     query = select(mymodel)
#     try:
#         # トランザクションを開始
#         with session.begin():
#             df = pd.read_sql_query(query, con=engine)
#             print(df)
#             result_json = df.to_json(orient='records', force_ascii=False)

#     except sqlalchemy.exc.IntegrityError:
#         print("一意制約違反により、挿入に失敗しました")
#         result_json = None

#     # セッションを閉じる
#     session.close()
#     return result_json

# crud.py
from sqlalchemy.orm import Session # Session をインポート

def myselectAll(mymodel):
    # session構築
    # Session = sessionmaker(bind=engine) # グローバルか、依存性注入で渡すのが望ましい
    # session = Session()
    with Session(engine) as session: # sessionmaker から直接セッションを取得し、コンテキストマネージャで自動クローズ
        try:
            # SQLAlchemy ORM を使ってオブジェクトのリストを取得
            results = session.scalars(select(mymodel)).all() # scalars() で単一エンティティを取得
            
            # オブジェクトを辞書のリストに変換 (internal_id を文字列に)
            result_list = []
            for item in results:
                # mymodels.py の Customers モデルが __init__ や __repr__ 以外に
                # to_dict() のようなメソッドを持つと便利
                # ここでは手動で辞書を作成
                result_list.append({
                    "internal_id": str(item.internal_id), # UUID を文字列に変換
                    "customer_id": item.customer_id,
                    "customer_name": item.customer_name,
                    "age": item.age,
                    "gender": item.gender,
                })
            
            # JSON文字列ではなく、Pythonのリストを直接返す
            # FastAPIが自動的にJSONにシリアライズしてくれる
            return result_list 

        except Exception as e:
            print(f"Error in myselectAll: {e}")
            # エラー発生時は空のリストまたは適切なエラーレスポンスを返す
            # FastAPIのエンドポイント側でHTTPExceptionをraiseするのも良い
            return [] 
    # session は with ブロックを抜ける際に自動的に close される


def myupdate(mymodel, values):
    # session構築
    Session = sessionmaker(bind=engine)
    session = Session()
    print('**************************************')
    print(mymodel.customer_id)
    print(values)
    customer_id = values.pop("customer_id")
    print(customer_id)
    print('**************************************')

    # query = "お見事！E0002の原因はこのクエリの実装ミスです。正しく実装しましょう"
    query = update(mymodel).where(mymodel.customer_id == customer_id).values(values)
    try:
        # トランザクションを開始
        with session.begin():
            result = session.execute(query)
    except sqlalchemy.exc.IntegrityError:
        print("一意制約違反により、挿入に失敗しました")
        session.rollback()
    # セッションを閉じる
    session.close()
    return "put"

def myupdate_orm(mymodel, internal_id: UUID, values: dict):
    with Session(engine) as session:
        try:
            db_item = session.get(mymodel, internal_id)
            if not db_item:
                return None
            
            for key, value in values.items():
                setattr(db_item, key, value) # ORMオブジェクトの属性を更新
            
            session.add(db_item) # 変更を追跡
            session.commit()
            session.refresh(db_item)
            return db_item
        except Exception as e:
            print(f"Error in myupdate_orm: {e}")
            session.rollback()
            return None

def mydelete(mymodel, customer_id):
    # session構築
    Session = sessionmaker(bind=engine)
    session = Session()
    query = delete(mymodel).where(mymodel.customer_id == customer_id)
    try:
        # トランザクションを開始
        with session.begin():
            result = session.execute(query)
    except sqlalchemy.exc.IntegrityError:
        print("一意制約違反により、挿入に失敗しました")
        session.rollback()

    # セッションを閉じる
    session.close()
    return customer_id + " is deleted"

def mydelete_orm(mymodel, internal_id: UUID) -> bool:
    with Session(engine) as session:
        try:
            db_item = session.get(mymodel, internal_id)
            if not db_item:
                return False # 見つからなければ False
            
            session.delete(db_item)
            session.commit()
            return True # 成功すれば True
        except Exception as e:
            print(f"Error in mydelete_orm: {e}")
            session.rollback()
            return False