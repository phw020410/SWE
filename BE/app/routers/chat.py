import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Query as URLQuery, Request, UploadFile
from fastapi.responses import Response

from app.dependencies import admin, current_user
from app.errors import AppError
from app.schemas import Query, QueryResponse
from app.services.markdown import export_markdown

router = APIRouter(tags=["질의·이력"])


def validate_id(value):
    if value is not None:
        try:
            uuid.UUID(value)
        except (ValueError, TypeError):
            raise AppError(400, "INVALID_INPUT", "대화 ID 형식이 올바르지 않습니다.")


@router.post("/api/query", response_model=QueryResponse)
async def query(body: Query, request: Request, user=Depends(current_user)):
    validate_id(body.conversation_id)
    return await request.app.state.chat.query(user, body)


@router.post("/api/image-query")
async def image(request: Request, file: Annotated[UploadFile, File()],
                conversationId: Annotated[str | None, Form()] = None, user=Depends(current_user)):
    validate_id(conversationId)
    try:
        raw = await file.read(request.app.state.settings.max_image_bytes + 1)
        return await request.app.state.chat.image(user, raw, file.filename, file.content_type, conversationId)
    finally:
        await file.close()


def serialize_history(conv):
    return {"conversationId": conv["id"], "title": conv["title"], "createdAt": conv["created_at"], "updatedAt": conv["updated_at"],
        "messages": [{"messageId": m["id"], "role": m["role"], "messageType": m["message_type"], "content": m["content"],
                      "createdAt": m["created_at"], "items": m.get("recommended_items", []), "imageAnalysis": m.get("image_analysis")} for m in conv.get("messages", [])]}


@router.get("/api/history")
async def history(request: Request, limit: Annotated[int, URLQuery(ge=1, le=100)] = 30,
                  offset: Annotated[int, URLQuery(ge=0)] = 0, user=Depends(current_user)):
    return [serialize_history(x) for x in await request.app.state.repository.history(user["id"], limit, offset)]


@router.get("/api/history/{conversation_id}/export")
async def export(conversation_id: str, request: Request, user=Depends(current_user)):
    validate_id(conversation_id)
    repo = request.app.state.repository
    conversation = await repo.full_conversation(user["id"], conversation_id)
    return Response(export_markdown(conversation), media_type="text/markdown; charset=utf-8",
                    headers={"Content-Disposition": f'attachment; filename="conversation-{conversation_id}.md"'})


@router.get("/api/admin/stats")
async def stats(request: Request, user=Depends(admin)):
    return await request.app.state.repository.stats()


@router.delete("/api/admin/cache", status_code=204)
async def clear_cache(request: Request, user=Depends(admin)):
    await request.app.state.repository.clear_cache()
    return Response(status_code=204)
