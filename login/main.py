from fastapi import FastAPI
from pydantic import BaseModel
from passlib.hash import bcrypt
from database import get_connection
import pymysql
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
# -------- Models --------

class User(BaseModel):
    email: str
    password: str

class Form(BaseModel):
    user_id: int
    data: str
from pydantic import BaseModel

class LoginUser(BaseModel):
    email: str
    password: str

# -------- Register --------
@app.post("/register")
def register(user: User):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM users WHERE email=%s", (user.email,))
        if cursor.fetchone():
            return {"status": "user exists"}

        hashed = bcrypt.hash(user.password)

        cursor.execute(
            "INSERT INTO users (email, password) VALUES (%s, %s)",
            (user.email, hashed)
        )

        conn.commit()
        return {"status": "success"}

    except Exception as e:
        return {"error": str(e)}

    finally:
        cursor.close()
        conn.close()

# -------- Login --------
@app.post("/login")
def login(user: LoginUser):
    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    cursor.execute("SELECT * FROM users WHERE email=%s", (user.email,))
    db_user = cursor.fetchone()

    if not db_user:
        return {"status": "not found"}

    if not bcrypt.verify(user.password, db_user["password"]):
        return {"status": "wrong password"}

    return {
        "status": "success",
        "email": db_user["email"],
        "id": db_user["id"]
    }

# # Enable CORS for frontend (Angular)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChangePassword(BaseModel):
    user_id: int
    old_password: str
    new_password: str


# -------- changer mdp --------
class ChangePassword(BaseModel):
    email: str
    old_password: str
    new_password: str


@app.post("/forgot-password")
def change_password(data: dict):
    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    cursor.execute("SELECT * FROM users WHERE email=%s", (data["email"],))
    user = cursor.fetchone()

    if not user:
        return {"status": "email not found"}

    new_hashed = bcrypt.hash(data["new_password"])

    cursor.execute(
        "UPDATE users SET password=%s WHERE email=%s",
        (new_hashed, data["email"])
    )
    conn.commit()

    return {"status": "password updated"}


    #----------- change password baad login 
@app.post("/change-password-auth")
def change_password_auth(data: dict):

    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    cursor.execute("SELECT * FROM users WHERE email=%s", (data.get("email"),))
    db_user = cursor.fetchone()

    if not db_user:
        return {"status": "user not found"}

    # ❌ vérification ancien mot de passe
    if not bcrypt.verify(data["old_password"], db_user["password"]):
        return {"status": "wrong old password"}

    # ❌ same password
    if bcrypt.verify(data["new_password"], db_user["password"]):
        return {"status": "same password"}

    # ✅ hash new password
    new_hashed = bcrypt.hash(data["new_password"])

    # ✅ update
    cursor.execute(
        "UPDATE users SET password=%s WHERE email=%s",
        (new_hashed, data.get("email"))
    )
    conn.commit()

    return {"status": "password updated"}

@app.post("/delete-account")
def delete_account(data: dict):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM users WHERE email=%s", (data.get("email"),))
    conn.commit()

    return {"status": "account deleted"}