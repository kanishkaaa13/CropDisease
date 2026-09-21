"""Local farmer/officer chat API with REST polling fallback and WebSocket delivery."""
from __future__ import annotations

import asyncio
import io
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Header, HTTPException, Query, UploadFile, WebSocket, WebSocketDisconnect, status
from PIL import Image
from sqlalchemy.orm import Session

from app.db.connection import get_db, SessionLocal
from app.db.models import AIResult, Conversation, ConversationStatus, Farm, Message, User, UserRole
from app.models.schemas import (
    ChatConversationCreate,
    ChatConversationResponse,
    ChatMessageCreate,
    ChatMessageResponse,
    ChatPageResponse,
)

router = APIRouter()
ws_router = APIRouter()
MAX_ATTACHMENT_SIZE = 5 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}


class ChatConnectionManager:
    def __init__(self) -> None:
        self.connections: dict[str, set[WebSocket]] = {}
        self.lock = asyncio.Lock()

    async def connect(self, conversation_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self.lock:
            self.connections.setdefault(conversation_id, set()).add(websocket)

    async def disconnect(self, conversation_id: str, websocket: WebSocket) -> None:
        async with self.lock:
            sockets = self.connections.get(conversation_id, set())
            sockets.discard(websocket)
            if not sockets:
                self.connections.pop(conversation_id, None)

    async def broadcast(self, conversation_id: str, payload: dict) -> None:
        async with self.lock:
            sockets = list(self.connections.get(conversation_id, set()))
        for socket in sockets:
            try:
                await socket.send_json(payload)
            except Exception:
                await self.disconnect(conversation_id, socket)


manager = ChatConnectionManager()


def _schedule_broadcast(conversation_id: str, payload: dict) -> None:
    """Broadcast when called from an async request; REST still succeeds without sockets."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return
    loop.create_task(manager.broadcast(conversation_id, payload))


def _user_id(user_id: Optional[str], header_user_id: Optional[str]) -> str:
    resolved = user_id or header_user_id
    if not resolved:
        raise HTTPException(status_code=401, detail="Demo user identity is required via user_id or X-User-ID")
    return resolved


def _get_user(db: Session, user_id: str) -> User:
    user = db.query(User).filter(User.id == user_id, User.is_active.is_(True)).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user


def _conversation_for_user(db: Session, conversation_id: str, user_id: str) -> Conversation:
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation or user_id not in {conversation.farmer_id, conversation.officer_id}:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


def _message_response(message: Message) -> ChatMessageResponse:
    return ChatMessageResponse(
        id=message.id,
        conversation_id=message.conversation_id,
        sender_id=message.sender_id,
        sender_role=message.sender_role,
        body=message.body,
        attachment_url=message.attachment_url,
        lang=message.lang,
        created_at=message.created_at,
        read_at=message.read_at,
    )


def _conversation_response(conversation: Conversation, db: Session, user_id: str) -> ChatConversationResponse:
    unread = db.query(Message).filter(
        Message.conversation_id == conversation.id,
        Message.sender_id != user_id,
        Message.read_at.is_(None),
    ).count()
    latest = db.query(Message).filter(Message.conversation_id == conversation.id).order_by(Message.created_at.desc()).first()
    scan = db.query(AIResult).filter(AIResult.id == conversation.scan_id).first() if conversation.scan_id else None
    image_url = None
    if scan and scan.observation and scan.observation.image_urls:
        image_url = scan.observation.image_urls[0]
    return ChatConversationResponse(
        id=conversation.id,
        farm_id=conversation.farm_id,
        farmer_id=conversation.farmer_id,
        officer_id=conversation.officer_id,
        scan_id=conversation.scan_id,
        status=conversation.status.value if hasattr(conversation.status, "value") else str(conversation.status),
        created_at=conversation.created_at,
        unread_count=unread,
        last_message=_message_response(latest) if latest else None,
        scan_label=scan.disease_label if scan else None,
        scan_image_url=image_url,
        heat_map_url=scan.heat_map_url if scan else None,
    )


@router.post("/chat/conversations", response_model=ChatConversationResponse)
def create_conversation(
    payload: ChatConversationCreate,
    user_id: Optional[str] = Query(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    db: Session = Depends(get_db),
):
    requester_id = _user_id(user_id, x_user_id)
    requester = _get_user(db, requester_id)
    farm = db.query(Farm).filter(Farm.id == payload.farm_id).first()
    if not farm or farm.owner_id != requester_id:
        raise HTTPException(status_code=403, detail="User does not own this farm")

    officer = db.query(User).filter(User.id == payload.officer_id, User.role == UserRole.officer, User.is_active.is_(True)).first()
    if not officer:
        raise HTTPException(status_code=400, detail="A valid active officer is required")
    if payload.scan_id:
        scan = db.query(AIResult).filter(AIResult.id == payload.scan_id).first()
        if not scan or not scan.observation or scan.observation.crop.farm_id != farm.id:
            raise HTTPException(status_code=400, detail="Scan does not belong to the selected farm")

    existing = db.query(Conversation).filter(
        Conversation.farm_id == farm.id,
        Conversation.farmer_id == requester.id,
        Conversation.officer_id == officer.id,
        Conversation.scan_id == payload.scan_id,
        Conversation.status == ConversationStatus.open,
    ).first()
    if existing:
        return _conversation_response(existing, db, requester_id)

    conversation = Conversation(
        farm_id=farm.id,
        farmer_id=requester.id,
        officer_id=officer.id,
        scan_id=payload.scan_id,
        status=ConversationStatus.open,
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return _conversation_response(conversation, db, requester_id)


@router.get("/chat/conversations", response_model=list[ChatConversationResponse])
def list_conversations(
    user_id: Optional[str] = Query(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    db: Session = Depends(get_db),
):
    requester_id = _user_id(user_id, x_user_id)
    _get_user(db, requester_id)
    conversations = db.query(Conversation).filter(
        (Conversation.farmer_id == requester_id) | (Conversation.officer_id == requester_id)
    ).order_by(Conversation.created_at.desc()).all()
    return [_conversation_response(item, db, requester_id) for item in conversations]


@router.get("/chat/conversations/{conversation_id}/messages", response_model=ChatPageResponse)
def get_messages(
    conversation_id: str,
    user_id: Optional[str] = Query(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    requester_id = _user_id(user_id, x_user_id)
    _conversation_for_user(db, conversation_id, requester_id)
    messages = db.query(Message).filter(Message.conversation_id == conversation_id).order_by(Message.created_at.asc()).offset(offset).limit(limit).all()
    total = db.query(Message).filter(Message.conversation_id == conversation_id).count()
    return ChatPageResponse(items=[_message_response(item) for item in messages], total=total, offset=offset, limit=limit)


@router.post("/chat/conversations/{conversation_id}/messages", response_model=ChatMessageResponse)
def send_message(
    conversation_id: str,
    payload: ChatMessageCreate,
    user_id: Optional[str] = Query(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    db: Session = Depends(get_db),
):
    requester_id = _user_id(user_id, x_user_id)
    conversation = _conversation_for_user(db, conversation_id, requester_id)
    sender = _get_user(db, requester_id)
    body = (payload.body or "").strip()
    if not body and not payload.attachment_url:
        raise HTTPException(status_code=422, detail="Message body or attachment is required")
    message = Message(
        conversation_id=conversation.id,
        sender_id=sender.id,
        sender_role=sender.role.value if hasattr(sender.role, "value") else str(sender.role),
        body=body,
        attachment_url=payload.attachment_url,
        lang=payload.lang or sender.language_pref or "en",
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    response = _message_response(message)
    # REST remains authoritative if no WebSocket clients are connected.
    _schedule_broadcast(conversation.id, {"type": "message", "message": response.model_dump(mode="json")})
    return response


@router.post("/chat/conversations/{conversation_id}/read")
def mark_read(
    conversation_id: str,
    user_id: Optional[str] = Query(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    db: Session = Depends(get_db),
):
    requester_id = _user_id(user_id, x_user_id)
    _conversation_for_user(db, conversation_id, requester_id)
    now = datetime.now(timezone.utc)
    count = db.query(Message).filter(
        Message.conversation_id == conversation_id,
        Message.sender_id != requester_id,
        Message.read_at.is_(None),
    ).update({Message.read_at: now}, synchronize_session=False)
    db.commit()
    _schedule_broadcast(conversation_id, {"type": "read", "user_id": requester_id, "read_at": now.isoformat()})
    return {"marked_read": count}


@router.post("/chat/attachments")
async def upload_attachment(
    file: UploadFile = File(...),
    user_id: Optional[str] = Query(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    db: Session = Depends(get_db),
):
    requester_id = _user_id(user_id, x_user_id)
    _get_user(db, requester_id)
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Only JPEG, PNG, and WEBP images are allowed")
    contents = await file.read(MAX_ATTACHMENT_SIZE + 1)
    if len(contents) > MAX_ATTACHMENT_SIZE:
        raise HTTPException(status_code=413, detail="Attachment exceeds the 5 MB limit")
    try:
        Image.open(io.BytesIO(contents)).verify()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Attachment is not a valid image") from exc
    folder = Path(__file__).parent.parent.parent / "uploads" / "chat"
    folder.mkdir(parents=True, exist_ok=True)
    suffix = Path(file.filename or "attachment.jpg").suffix.lower() or ".jpg"
    filename = f"{uuid.uuid4()}{suffix}"
    (folder / filename).write_bytes(contents)
    return {"attachment_url": f"/uploads/chat/{filename}", "size": len(contents), "content_type": file.content_type}


@ws_router.websocket("/ws/chat/{conversation_id}")
async def chat_socket(websocket: WebSocket, conversation_id: str):
    user_id = websocket.query_params.get("user_id") or websocket.headers.get("x-user-id")
    db = SessionLocal()
    try:
        if not user_id:
            await websocket.close(code=4401, reason="user_id is required")
            return
        conversation = _conversation_for_user(db, conversation_id, user_id)
        _get_user(db, user_id)
        await manager.connect(conversation.id, websocket)
        await websocket.send_json({"type": "connected", "conversation_id": conversation.id})
        while True:
            payload = await websocket.receive_json()
            if payload.get("type") == "typing":
                await manager.broadcast(conversation.id, {"type": "typing", "user_id": user_id, "is_typing": bool(payload.get("is_typing"))})
            elif payload.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        pass
    except HTTPException:
        await websocket.close(code=4403, reason="conversation access denied")
    except Exception:
        try:
            await websocket.close(code=1011, reason="chat temporarily unavailable")
        except Exception:
            pass
    finally:
        await manager.disconnect(conversation_id, websocket)
        db.close()
