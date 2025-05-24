from sqlalchemy import String, Integer, ForeignKey, DateTime, Date, func # DateTime, Date, func をインポート
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
import uuid
from sqlalchemy.dialects.mysql import CHAR as MYSQL_CHAR, INTEGER # 必要であれば使う
from sqlalchemy.types import UUID as SQLAlchemyUUID # MySQLネイティブUUIDサポートを期待
from datetime import datetime # datetime をインポート

class Base(DeclarativeBase):
    pass

class Customers(Base):
    __tablename__ = 'customers'

    # MySQLはCHAR(36)やBINARY(16)でUUIDを扱えるので、標準のSQLAlchemyUUIDを使用
    # (as_uuid=True) でPython側ではuuid.UUIDオブジェクトとして扱われる
    internal_id: Mapped[uuid.UUID] = mapped_column(
        SQLAlchemyUUID(as_uuid=True).with_variant(MYSQL_CHAR(36), "mysql"),
        primary_key=True, default=uuid.uuid4
    )
    # customer_id は従来のIDとして、ユニークかつ非NULLを推奨
    customer_id: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    customer_name: Mapped[str] = mapped_column(String(100), nullable=False) # 名前も非NULL推奨
    age: Mapped[int] = mapped_column(Integer, nullable=True) # 年齢はNULL許容の場合も
    gender: Mapped[str] = mapped_column(String(10), nullable=True) # 性別もNULL許容の場合も

    def __repr__(self):
        return (f"<Customer(internal_id='{self.internal_id}', "
                f"customer_id='{self.customer_id}', name='{self.customer_name}')>")

class Items(Base):
    __tablename__ = 'items'
    # item_id は文字列型の主キー
    item_id: Mapped[str] = mapped_column(String(50), primary_key=True) # 文字長を適切に
    item_name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True) # 商品名は非NULLかつユニーク推奨
    price: Mapped[int] = mapped_column(Integer, nullable=False) # 価格は非NULL推奨

    def __repr__(self):
        return f"<Item(item_id='{self.item_id}', name='{self.item_name}', price={self.price})>"

class Purchases(Base):
    __tablename__ = 'purchases'
    # purchase_id は自動インクリメントの整数主キーが良い場合が多い
    purchase_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # 外部キーは customers テーブルの internal_id を参照するのが新しい設計では自然
    # ここでは元の customer_id を参照する形を残すが、internal_id 参照を検討
    customer_internal_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("customers.internal_id"), nullable=False) # internal_id を参照
    # purchase_date は DateTime型を推奨
    purchase_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now()) # デフォルトで現在時刻

    def __repr__(self):
        return (f"<Purchase(purchase_id={self.purchase_id}, "
                f"customer_internal_id='{self.customer_internal_id}', date='{self.purchase_date}')>")

class PurchaseDetails(Base):
    __tablename__ = 'purchase_details'
    # 複合主キーまたは自動インクリメントの単一主キーを検討
    # ここでは複合主キーのまま
    purchase_id: Mapped[int] = mapped_column(ForeignKey("purchases.purchase_id"), primary_key=True)
    item_id: Mapped[str] = mapped_column(ForeignKey("items.item_id"), primary_key=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)

    def __repr__(self):
        return (f"<PurchaseDetail(purchase_id={self.purchase_id}, "
                f"item_id='{self.item_id}', quantity={self.quantity})>")