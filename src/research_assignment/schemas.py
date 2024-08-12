from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class PasswordReset(BaseModel):
    username: str
    new_password: str

class SubscriptionCreate(BaseModel):
    user_id: int
    plan_id: int
    active: bool = True

    class Config:
        orm_mode = True

class UserResponse(BaseModel):
    username: str
    email: str

    class Config:
        orm_mode = True

class PlanCreate(BaseModel):
    magazine_id: int
    name: str
    price: int
    discount: int = 0

    class Config:
        orm_mode = True

class MagazineCreate(BaseModel):
    title: str
    description: str

    class Config:
        orm_mode = True

class SubscriptionUpdate(BaseModel):
    plan_id: int = None
    active: bool = None

    class Config:
        orm_mode = True