from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from libsql_client import create_client, Client, ResultSet
from pydantic import BaseModel
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()

# Configuración de la conexión a Turso
client: Client = create_client(
    url=os.getenv("TURSO_DATABASE_URL", ""),
    auth_token=os.getenv("TURSO_AUTH_TOKEN", "")
)

# Modelo Pydantic para las notas
class NoteModel(BaseModel):
    content: str

class NoteResponse(BaseModel):
    id: int
    content: str

@app.on_event("startup")
async def startup() -> None:
    # Crear tabla si no existe
    await client.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL
        )
    """)

@app.get("/")
async def root() -> Dict[str, str]:
    return {"message": "API conectada a Turso"}

@app.get("/notes", response_model=List[NoteResponse])
async def get_notes() -> List[Dict[str, Any]]:
    result: ResultSet = await client.execute("SELECT * FROM notes")
    return [{"id": row[0], "content": row[1]} for row in result.rows]

@app.post("/notes", response_model=Dict[str, Any])
async def create_note(note: NoteModel) -> Dict[str, Any]:
    result: ResultSet = await client.execute(
        "INSERT INTO notes (content) VALUES (?)", 
        [note.content]
    )
    return {"message": "Nota creada", "id": result.last_insert_rowid}

@app.get("/notes/{note_id}", response_model=NoteResponse)
async def get_note(note_id: int) -> Dict[str, Any]:
    result: ResultSet = await client.execute(
        "SELECT * FROM notes WHERE id = ?", 
        [note_id]
    )
    if not result.rows:
        raise HTTPException(status_code=404, detail="Nota no encontrada")
    return {"id": result.rows[0][0], "content": result.rows[0][1]} 