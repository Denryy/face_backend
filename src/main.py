import json
import math
from fastapi import FastAPI, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .models import User, FaceTemplate, AccessEvent
from .schemas import (
    UserCreate,
    UserOut,
    FaceCreate,
    AccessCheckRequest,
    AccessCheckResponse,
    EventCreate,
)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Face ID Access Control Backend")
templates = Jinja2Templates(directory="src/templates")

FACE_MATCH_THRESHOLD = 0.65


def cosine_similarity(a, b):
    if len(a) != len(b):
        return 0.0

    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot / (norm_a * norm_b)


@app.get("/")
def root():
    return {"status": "ok", "message": "Face backend is running"}


@app.post("/api/users", response_model=UserOut)
def create_user(data: UserCreate, db: Session = Depends(get_db)):
    user = User(
        full_name=data.full_name,
        department=data.department,
        position=data.position,
        status=data.status,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.get("/api/users", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db)):
    return db.query(User).order_by(User.id.desc()).all()


@app.post("/api/users/{user_id}/faces")
def add_face(user_id: int, data: FaceCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    face = FaceTemplate(
        user_id=user_id,
        embedding=json.dumps(data.embedding),
        embedding_model=data.embedding_model,
        quality_score=data.quality_score,
        status="active",
    )

    db.add(face)
    db.commit()
    db.refresh(face)

    return {
        "id": face.id,
        "user_id": face.user_id,
        "status": face.status,
        "embedding_model": face.embedding_model,
    }


@app.post("/api/access/check-face", response_model=AccessCheckResponse)
def check_face(data: AccessCheckRequest, db: Session = Depends(get_db)):
    faces = db.query(FaceTemplate).filter(FaceTemplate.status == "active").all()

    best_face = None
    best_user = None
    best_similarity = 0.0

    for face in faces:
        stored_embedding = json.loads(face.embedding)
        similarity = cosine_similarity(data.embedding, stored_embedding)

        if similarity > best_similarity:
            best_similarity = similarity
            best_face = face
            best_user = db.query(User).filter(User.id == face.user_id).first()

    decision = "denied"
    reason = "unknown_face"
    unlock_duration_sec = 0
    user_id = None
    full_name = None

    if best_face and best_similarity < FACE_MATCH_THRESHOLD:
        reason = "low_similarity"

    if best_face and best_similarity >= FACE_MATCH_THRESHOLD:
        user_id = best_user.id
        full_name = best_user.full_name

        if best_user.status != "active":
            decision = "denied"
            reason = "user_blocked"
        else:
            decision = "allowed"
            reason = "access_granted"
            unlock_duration_sec = 3

    event = AccessEvent(
        user_id=user_id,
        access_point_id=data.access_point_id,
        controller_id=data.controller_id,
        decision=decision,
        reason=reason,
        similarity=best_similarity,
        liveness_score=data.liveness_score,
    )

    db.add(event)
    db.commit()

    return AccessCheckResponse(
        decision=decision,
        reason=reason,
        user_id=user_id,
        full_name=full_name,
        similarity=round(best_similarity, 4),
        unlock_duration_sec=unlock_duration_sec,
    )


@app.post("/api/events")
def create_event(data: EventCreate, db: Session = Depends(get_db)):
    event = AccessEvent(
        user_id=data.user_id,
        access_point_id=data.access_point_id,
        controller_id=data.controller_id,
        decision=data.decision,
        reason=data.reason,
        similarity=data.similarity,
        liveness_score=data.liveness_score,
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    return {"id": event.id, "status": "saved"}


@app.get("/api/events")
def list_events(db: Session = Depends(get_db)):
    events = db.query(AccessEvent).order_by(AccessEvent.id.desc()).limit(100).all()

    return [
        {
            "id": e.id,
            "timestamp": e.timestamp,
            "user_id": e.user_id,
            "access_point_id": e.access_point_id,
            "controller_id": e.controller_id,
            "decision": e.decision,
            "reason": e.reason,
            "similarity": e.similarity,
            "liveness_score": e.liveness_score,
        }
        for e in events
    ]


@app.get("/admin", response_class=HTMLResponse)
def admin_page(request: Request, db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.id.desc()).all()
    events = db.query(AccessEvent).order_by(AccessEvent.id.desc()).limit(20).all()

    return templates.TemplateResponse(
        name="admin.html",
        request=request,
        context={
            "users": users,
            "events": events,
        },
    )


@app.post("/admin/users")
def admin_create_user(
    full_name: str = Form(...),
    department: str = Form(""),
    position: str = Form(""),
    db: Session = Depends(get_db),
):
    user = User(
        full_name=full_name,
        department=department,
        position=position,
        status="active",
    )
    db.add(user)
    db.commit()

    return RedirectResponse(url="/admin", status_code=303)
