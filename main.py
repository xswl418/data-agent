from fastapi import FastAPI
from pydantic import BaseModel
from database import init_db, get_tasks
from agent import chat

app = FastAPI()
init_db()

class AskRequest(BaseModel):
    question: str

@app.post("/ask")
def ask(req: AskRequest):
    reply, history, report = chat(history=[], user_input=req.question)
    return {"reply": reply, "report": report}

@app.get("/tasks")
def tasks():
    return get_tasks()