# pyrefly: ignore [missing-import]
from fastapi import FastAPI, Response, HTTPException, Request, Depends
# pyrefly: ignore [missing-import]
from fastapi.responses import JSONResponse
# pyrefly: ignore [missing-import]
from pydantic import BaseModel
import os
# pyrefly: ignore [missing-import]
import psycopg
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv
# pyrefly: ignore [missing-import]
from psycopg.rows import dict_row
# pyrefly: ignore [missing-import]
from supabase import create_client, Client
# pyrefly: ignore [missing-import]
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

app = FastAPI()
load_dotenv()
DATABASE_URL=os.getenv("DATABASE_URL")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_db():
    """Helper connection function that returns rows formatted like dictionaries."""
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)

def init_db():
    """Creates table and seeds default tasks if the database is empty."""
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    done BOOLEAN DEFAULT FALSE
                );
            """)

            cursor.execute("SELECT COUNT(*) AS count FROM tasks;")
            row_count = cursor.fetchone()[0]

            if row_count == 0:
                cursor.execute("INSERT INTO tasks (title, done) VALUES (%s, %s)", ("Master Docker", False))
                cursor.execute("INSERT INTO tasks (title, done) VALUES (%s, %s)", ("Learn Postgres", False))
                cursor.execute("INSERT INTO tasks (title, done) VALUES (%s, %s)", ("Build an API", True))

init_db()

class UserCredentials(BaseModel):
    email: str
    password: str

class TaskCreate(BaseModel):
    title: str | None = None 

class TaskUpdate(BaseModel):
    title: str | None = None
    done: bool | None = None


security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Reusable dependency to verify the token and inject the user."""
    token = credentials.credentials
    try:
        # Ask Supabase to verify the token
        response = supabase.auth.get_user(token)
        return response.user
    except Exception:
        raise HTTPException(status_code=401, detail={"error": "Invalid or expired token"})

@app.get("/")
def read_root():
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/public/info", status_code=200)
def public_info():
    """A public lobby anyone can enter."""
    return {"message": "Welcome stranger! This info is public."}

@app.get("/protected/profile")
def protected_profile(user = Depends(get_current_user)):
    """A locked door, now protected by our reusable guard."""
    return {
        "id": user.id,
        "email": user.email,
        "created_at": user.created_at
    }

@app.get("/protected/dashboard")
def protected_dashboard(user = Depends(get_current_user)):
    """A second protected door to prove middleware reusability."""
    return {"message": f"Welcome to your private dashboard, {user.email}!"}

@app.get("/tasks")
def get_all_tasks():
    """Returns a list of all tasks in the in-memory database."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM tasks")

    tasks = [dict(row) for row in cursor.fetchall()]

    cursor.close()
    conn.close()

    return tasks

@app.get("/tasks/{id}", responses={404: {"description": "Task not found"}})
def get_task(id: int):
    """Returns a single task matching the provided ID."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM tasks WHERE id = %s", (id,))
    row = cursor.fetchone()

    cursor.close()
    conn.close()
    
    if row is None:
        return JSONResponse(status_code=404, content={"error": f"Task {id} not found"})

    return dict(row)

@app.post("/auth/signup", status_code=201)
def signup(credentials: UserCredentials):
    if not credentials.email or not credentials.password:
        raise HTTPException(status_code=400, detail="Email & Password are required!")
    
    try:
        response = supabase.auth.sign_up({
            "email": credentials.email,
            "password": credentials.password
        })
        return response.user
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/auth/login", status_code=200)
def login(credentials: UserCredentials):
    if not credentials.email or not credentials.password:
        raise HTTPException(status_code=400, detail="Email and password are required")
    
    try:
        response = supabase.auth.sign_in_with_password({
            "email": credentials.email,
            "password": credentials.password
        })
        return {
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token
        }
    except Exception:
        raise HTTPException(status_code=401, detail={"error": "Invalid login credentials"})

@app.post("/auth/logout", status_code=204)
def logout(user = Depends(get_current_user)):
    """Ends the user's session."""
    try:
        supabase.auth.sign_out()
        return Response(status_code=204)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/tasks", status_code=201, responses={400: {"description": "Invalid input - Title is missing or empty"}})
def create_task(task_in: TaskCreate):
    """Creates a new task and assigns it a unique ID."""
    if not task_in.title or not task_in.title.strip():
        return JSONResponse(status_code=400, content={"error": "Title is missing or empty"})
    
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO tasks (title, done) VALUES (%s, %s) RETURNING *;",
        (task_in.title.strip(), False)
    )
    new_task = dict(cursor.fetchone())
    conn.commit()
    
    cursor.close()
    conn.close()

    return JSONResponse(status_code=201, content=new_task)

@app.put("/tasks/{id}" , responses={400: {"description": "Invalid body"}, 404: {"description": "Task not found"}})
def update_task(id: int, task_in: TaskUpdate):
    """Updates the title or completion status of an existing task."""
    if task_in.title is None and task_in.done is None:
        return JSONResponse(status_code=400, content={"error": "Body cannot be empty"})

    if task_in.title is not None and not task_in.title.strip():
        return JSONResponse(status_code=400, content={"error": "Title cannot be empty"})
    
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM tasks WHERE id = %s", (id,))
    row = cursor.fetchone()

    if row is None:
        cursor.close()
        conn.close()
        return JSONResponse(status_code=404, content={"error": f"Task {id} not found"})

    existing_task = dict(row)

    new_title = task_in.title.strip() if task_in.title is not None else existing_task["title"]

    new_done = task_in.done if task_in.done is not None else existing_task["done"]
    
    cursor.execute(
        "UPDATE tasks SET title = %s, done = %s WHERE id = %s RETURNING *",
        (new_title, new_done, id)
    )
    updated_task = dict(cursor.fetchone())
    conn.commit()
    cursor.close()
    conn.close()

    return updated_task
    
@app.delete("/tasks/{id}", responses={404: {"description": "Task not found"}})
def delete_task(id: int):
    """Deletes a task from the list based on its ID."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM tasks WHERE id = %s", (id,))
    deleted_count = cursor.rowcount
    conn.commit()
    cursor.close()
    conn.close()

    if deleted_count == 0:
        return JSONResponse(status_code=404, content={"error": f"Task{id} not found"})

    return Response(status_code = 204)