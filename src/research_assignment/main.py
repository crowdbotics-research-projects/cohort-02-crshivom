from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session, sessionmaker

from models import Base, Magazine, Subscription, User, Plan
from database import engine  # Importing the engine and SessionLocal from database.py
from schemas import (
    SubscriptionUpdate,
    UserCreate,
    UserLogin,
    SubscriptionCreate,
    PasswordReset,
    UserResponse,
    PlanCreate,
    MagazineCreate,
)
from auth import get_password_hash, verify_password, create_access_token
from typing import List

# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


app = FastAPI()

# Ensure the tables are created
Base.metadata.create_all(bind=engine)


@app.get("/")
def read_root():
    return {"message": "Welcome to the Magazine Subscription Service"}


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/magazines")
async def list_magazines(db: Session = Depends(get_db)):
    return db.query(Magazine).all()


@app.get("/users", response_model=List[UserResponse])
def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users


@app.post("/register", response_model=dict)
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    hashed_password = get_password_hash(user.password)
    new_user = User(
        username=user.username, email=user.email, hashed_password=hashed_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"username": new_user.username, "email": new_user.email}


@app.post("/login", response_model=dict)
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    access_token = create_access_token(data={"sub": db_user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/reset-password", response_model=dict)
def reset_password(reset: PasswordReset, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == reset.username).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    db_user.hashed_password = get_password_hash(reset.new_password)
    db.commit()
    return {"msg": "Password reset successful"}


@app.post("/subscriptions/", response_model=SubscriptionCreate)
async def create_subscription(
    subscription: SubscriptionCreate, db: Session = Depends(get_db)
):
    """
    Create a new subscription
    BODY:{
        "user_id": 1,
        "plan_id": 1,
        "active": true
        }
    """
    # Verify the user exists
    db_user = db.query(User).filter(User.id == subscription.user_id).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Verify the plan exists
    db_plan = db.query(Plan).filter(Plan.id == subscription.plan_id).first()
    if not db_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found"
        )

    # Create the subscription
    db_subscription = Subscription(**subscription.dict())
    db.add(db_subscription)
    db.commit()
    db.refresh(db_subscription)

    return db_subscription


@app.post("/plans/", response_model=PlanCreate)
async def create_plan(plan: PlanCreate, db: Session = Depends(get_db)):
    """
    Create a new plan
    BODY:{
        "magazine_id": 1,
        "name": "Monthly Subscription",
        "price": 10,
        "discount": 0
        }
    """
    # Verify the magazine exists
    db_magazine = db.query(Magazine).filter(Magazine.id == plan.magazine_id).first()
    if not db_magazine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Magazine not found"
        )

    # Create the plan
    db_plan = Plan(**plan.dict())
    db.add(db_plan)
    db.commit()
    db.refresh(db_plan)

    return db_plan


@app.post("/magazines/", response_model=MagazineCreate)
async def create_magazine(magazine: MagazineCreate, db: Session = Depends(get_db)):
    """
    Create a new magazine
    BODY:{
        "title": "Tech Monthly",
        "description": "A magazine dedicated to the latest in tech."
        }

    """
    # Check if a magazine with the same title already exists
    db_magazine = db.query(Magazine).filter(Magazine.title == magazine.title).first()
    if db_magazine:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Magazine with this title already exists",
        )

    # Create the magazine
    db_magazine = Magazine(**magazine.dict())
    db.add(db_magazine)
    db.commit()
    db.refresh(db_magazine)

    return db_magazine


@app.get("/subscriptions/{user_id}", response_model=List[SubscriptionCreate])
async def get_user_subscriptions(user_id: int, db: Session = Depends(get_db)):
    """
    Get all subscriptions for a user
    URL: /subscriptions/1
    """
    subscriptions = db.query(Subscription).filter(Subscription.user_id == user_id).all()
    if not subscriptions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No subscriptions found for this user",
        )
    return subscriptions


@app.put("/subscriptions/{subscription_id}", response_model=SubscriptionCreate)
async def update_subscription(
    subscription_id: int,
    subscription: SubscriptionUpdate,
    db: Session = Depends(get_db),
):
    """
    Update a subscription
    URL: /subscriptions/1
    BODY:{
        "plan_id": 2,
        "active": false
    """
    db_subscription = (
        db.query(Subscription).filter(Subscription.id == subscription_id).first()
    )
    if not db_subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found"
        )

    if subscription.plan_id is not None:
        db_subscription.plan_id = subscription.plan_id
    if subscription.active is not None:
        db_subscription.active = subscription.active

    db.commit()
    db.refresh(db_subscription)

    return db_subscription


# Assuming this is a placeholder function to get the current authenticated user.
def get_current_user(db: Session = Depends(get_db)):
    # In a real application, this would retrieve the current user based on the authentication token.
    # Example: user = db.query(User).filter(User.id == user_id_from_token).first()
    user = (
        db.query(User).filter(User.id == 1).first()
    )  # Placeholder: Replace with actual authentication logic
    return user


@app.delete("/subscriptions/{subscription_id}", response_model=dict)
async def delete_subscription(
    subscription_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a subscription only if it belongs to the current user
    URL: /subscriptions/1
    """
    db_subscription = (
        db.query(Subscription).filter(Subscription.id == subscription_id).first()
    )

    if not db_subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found"
        )

    # Check if the subscription belongs to the current user
    if db_subscription.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this subscription",
        )

    db.delete(db_subscription)
    db.commit()

    return {"msg": "Subscription deleted successfully"}
