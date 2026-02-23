from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import Dict, Any, List
import json
import os
import time

app = FastAPI(title="ADSC CNN Leaderboard API")

LEADERBOARD_PATH = "leaderboard.json"
BOARD: Dict[str, Dict[str, Any]] = {}

def load_board() -> None:
    global BOARD
    if os.path.exists(LEADERBOARD_PATH):
        try:
            with open(LEADERBOARD_PATH, "r") as f:
                BOARD = json.load(f)
        except Exception:
            BOARD = {}
    else:
        BOARD = {}

def save_board() -> None:
    tmp = LEADERBOARD_PATH + ".tmp"
    with open(tmp, "w") as f:
        json.dump(BOARD, f, indent=2)
    os.replace(tmp, LEADERBOARD_PATH)

load_board()

class SubmitPayload(BaseModel):
    username: str = Field(..., min_length=1, max_length=40)
    test_acc: float = Field(..., ge=0.0, le=100.0)

def normalized_username(u: str) -> str:
    u = u.strip()
    # Keep it simple: collapse internal whitespace
    u = " ".join(u.split())
    return u

def public_entries() -> List[Dict[str, Any]]:
    entries = []
    for _, v in BOARD.items():
        entries.append({
            "username": v["username"],
            "best_test_acc": v["best_test_acc"],
            "updated_at": v["updated_at"],
        })
    entries.sort(key=lambda x: x["best_test_acc"], reverse=True)
    return entries

@app.get("/")
def root():
    return {"ok": True, "message": "ADSC CNN Leaderboard API is running."}

@app.get("/leaderboard")
def leaderboard():
    return {"ok": True, "leaderboard": public_entries()}

@app.post("/submit")
def submit(payload: SubmitPayload):
    username = normalized_username(payload.username)
    test_acc = float(payload.test_acc)

    if not username:
        return {"ok": False, "error": "Username cannot be empty."}

    now = int(time.time())

    existing = BOARD.get(username)
    if existing is None:
        BOARD[username] = {
            "username": username,
            "best_test_acc": test_acc,
            "updated_at": now,
        }
        save_board()
        return {
            "ok": True,
            "message": "New user added ✅",
            "your_best": test_acc,
            "leaderboard": public_entries(),
        }

    # Only update if improved
    if test_acc > float(existing["best_test_acc"]):
        existing["best_test_acc"] = test_acc
        existing["updated_at"] = now
        save_board()
        return {
            "ok": True,
            "message": "Updated (new best) ✅",
            "your_best": test_acc,
            "leaderboard": public_entries(),
        }

    return {
        "ok": True,
        "message": "Received (not higher than your best)",
        "your_best": float(existing["best_test_acc"]),
        "leaderboard": public_entries(),
    }