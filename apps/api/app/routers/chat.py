"""Chat-with-your-channel — streaming, grounded in the channel's own analysis + memory."""

from __future__ import annotations

import json
import uuid
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..ai import memory
from ..ai.llm import Tier, get_llm_provider
from ..db.session import get_db
from ..deps import current_org, require_feature
from ..models import Channel, Insight, Organization
from ..repositories.channels import ChannelRepository

router = APIRouter(prefix="/channels", tags=["chat"])

_SYSTEM = (
    "You are the creator's AI channel strategist. Answer questions about THIS channel using "
    "the provided analysis and history. Be specific, cite the data, and give actionable "
    "advice. If the data doesn't cover something, say so rather than inventing numbers."
)


class ChatIn(BaseModel):
    message: str


async def _latest_insight(db: AsyncSession, channel_id: uuid.UUID) -> dict | None:
    row = (
        await db.execute(
            select(Insight.payload)
            .where(Insight.channel_id == channel_id)
            .order_by(Insight.created_at.desc())
            .limit(1)
        )
    ).first()
    return row[0] if row else None


@router.post("/{channel_id}/chat")
async def chat(
    channel_id: uuid.UUID,
    body: ChatIn,
    org: Organization = Depends(current_org),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_feature("ai_chat")),
) -> StreamingResponse:
    channel: Channel | None = await ChannelRepository(db, org.id).get(channel_id)
    if channel is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found")

    payload = await _latest_insight(db, channel_id)
    relevant = await memory.retrieve_memories(db, channel_id=channel_id, query=body.message)

    context_parts = [f"CHANNEL: {channel.title or 'Channel'}"]
    if payload:
        context_parts.append("LATEST ANALYSIS:\n" + json.dumps(payload)[:4000])
    if relevant:
        context_parts.append(
            "RELEVANT HISTORY:\n" + "\n".join(f"- {m.summary}" for m in relevant)
        )
    system = _SYSTEM + "\n\n" + "\n\n".join(context_parts)

    llm = get_llm_provider()

    async def event_stream() -> AsyncIterator[bytes]:
        async for chunk in llm.stream_text(
            system=system,
            messages=[{"role": "user", "content": body.message}],
            tier=Tier.FLAGSHIP,
        ):
            # Server-Sent Events framing.
            yield f"data: {json.dumps({'delta': chunk})}\n\n".encode()
        yield b"data: {\"done\": true}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
