from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, UUID4, Field
import requests
import json
from db_control import crud, mymodels_MySQL as mymodels


class CustomerBase(BaseModel): # 作成時・更新時用のベースモデル
    customer_id: str # internal_id が主キーなので、これは通常の属性
    customer_name: str
    age: int
    gender: str

class CustomerCreate(CustomerBase):
    pass # 作成時は internal_id は自動生成

class CustomerUpdate(CustomerBase):
    pass # 更新時も internal_id はパスパラメータで指定

class CustomerResponse(CustomerBase): # レスポンス用モデル
    internal_id: UUID4 # DBから取得した internal_id を含める

    class Config:
        # orm_mode = True # SQLAlchemyモデルから自動変換するために必要 (v1)
        from_attributes = True # Pydantic v2

app = FastAPI()

# CORSミドルウェアの設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def index():
    return {"message": "FastAPI top page!"}


@app.post("/customers", response_model=CustomerResponse)
def create_customer(customer_data: CustomerCreate): # 入力は CustomerCreate
    # customer_data には internal_id は含まれない
    # crud.myinsert で internal_id は自動生成される想定
    new_customer_obj = crud.myinsert_orm(mymodels.Customers, customer_data.model_dump()) # model_dump() (v2) or dict() (v1)
    if not new_customer_obj:
        raise HTTPException(status_code=500, detail="Failed to create customer")
    return new_customer_obj # ORMオブジェクトをそのまま返す (FastAPIがシリアライズ)


# customer_id ではなく internal_id (UUID) をパスパラメータとして受け取る
@app.get("/customers/{internal_id}", response_model=CustomerResponse)
def read_one_customer(internal_id: UUID4): # パスパラメータの型を UUID4 に
    customer = crud.myselect_by_internal_id(mymodels.Customers, internal_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer # ORMオブジェクトをそのまま返す

@app.get("/allcustomers", response_model=list[CustomerResponse]) # response_model を指定
def read_all_customer():
    result_list = crud.myselectAll(mymodels.Customers)
    # crud.myselectAll が Python のリストを返すようになったので json.loads は不要
    if not result_list: # result_list が空の場合
        return []
    return result_list

@app.put("/customers/{internal_id}", response_model=CustomerResponse)
def update_customer(internal_id: UUID4, customer_data: CustomerUpdate):
    updated_customer = crud.myupdate_orm(mymodels.Customers, internal_id, customer_data.model_dump())
    if not updated_customer:
        raise HTTPException(status_code=404, detail="Customer not found or failed to update")
    return updated_customer


@app.delete("/customers/{internal_id}", status_code=204) # 成功時は No Content
def delete_customer(internal_id: UUID4):
    success = crud.mydelete_orm(mymodels.Customers, internal_id)
    if not success:
        raise HTTPException(status_code=404, detail="Customer not found")
    return # No Content なのでボディは返さない


@app.get("/fetchtest")
def fetchtest():
    response = requests.get('https://jsonplaceholder.typicode.com/users')
    return response.json()
