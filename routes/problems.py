from fastapi import APIRouter, HTTPException
from db.connection import get_connection
from models.schemas import ProblemOut

router = APIRouter()

@router.get("/problems", response_model = list[ProblemOut])
def list_problem():
    conn= get_connection()
    cur = conn.cursor(dictionary = True) 
    cur.execute("SELECT id, title, description, constraints, difficulty FROM problems")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

@router.get("/problems/{problem_id}", response_model=ProblemOut)
def get_problem(problem_id:int):
    conn = get_connection()
    cur =conn.cursor(dictionary =True)
    cur.execute("SELECT id, title, description, constraints, difficulty FROM problems WHERE id = %s",(problem_id,))
    row = cur.fetchone()
    conn.close()
    cur.close()
    if not row:
        raise HTTPException(status_code =404, detail= "problem not found")
    return row

