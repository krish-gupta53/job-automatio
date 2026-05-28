from typing import Literal

from fastapi import APIRouter
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field

from common import settings
from globals import CRITIC_PROMPT, SCRIPT_SYSTEM_PROMPT

# NOTE: File name is legacy (`api.ts`) but contains Python code.
from api import GeminiService

router = APIRouter(prefix="/api")
_client: AsyncIOMotorClient | None = None


def get_db():
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(settings.mongodb_uri)
    return _client[settings.mongodb_db]


class CreatorProfile(BaseModel):
    creator_id: str
    niche: str
    target_audience: str
    brand_voice: str
    goals: list[str] = []


class VideoPerformance(BaseModel):
    creator_id: str
    title: str
    topic: str
    hook_type: str
    tone: str
    duration_seconds: int = Field(le=180)
    likes: int = 0
    comments: int = 0
    shares: int = 0
    follows: int = 0
    views: int = 1
    notes: str = ""


class SourceText(BaseModel):
    creator_id: str
    title: str
    content: str
    kind: Literal["text", "web", "ocr"] = "text"


class ScriptRequest(BaseModel):
    creator_id: str
    topic: str
    goal: str
    audience: str
    vibe: str
    platform: str
    source_hint: str = ""
    max_duration_seconds: int = Field(default=180, le=180)


@router.get("/health")
async def health():
    return {"status": "ok", "service": "creatorpilot-ai"}


@router.post("/creator/profile")
async def save_profile(profile: CreatorProfile):
    db = get_db()
    await db.creator_profiles.update_one(
        {"creator_id": profile.creator_id},
        {"$set": profile.model_dump()},
        upsert=True,
    )
    return {"ok": True, "creator_id": profile.creator_id}


@router.post("/videos")
async def add_video(video: VideoPerformance):
    db = get_db()
    doc = video.model_dump()
    doc["engagement_score"] = (doc["likes"] + 2 * doc["comments"] + 3 * doc["shares"] + 4 * doc["follows"]) / max(doc["views"], 1)
    result = await db.videos.insert_one(doc)
    return {"ok": True, "id": str(result.inserted_id)}


@router.post("/sources/text")
async def add_source(source: SourceText):
    db = get_db()
    result = await db.sources.insert_one(source.model_dump())
    return {"ok": True, "id": str(result.inserted_id)}


@router.post("/learning/update/{creator_id}")
async def update_learning(creator_id: str):
    db = get_db()
    videos = await db.videos.find({"creator_id": creator_id}).sort("engagement_score", -1).limit(5).to_list(5)
    learnings = [f"Prefer topic={v['topic']}, hook={v['hook_type']}, tone={v['tone']}" for v in videos]
    await db.learning_memory.update_one(
        {"creator_id": creator_id},
        {"$set": {"creator_id": creator_id, "learnings": learnings}},
        upsert=True,
    )
    return {"ok": True, "learnings": learnings}


@router.post("/scripts/generate")
async def generate_script(request: ScriptRequest):
    db = get_db()
    profile = await db.creator_profiles.find_one({"creator_id": request.creator_id}) or {}
    videos = await db.videos.find({"creator_id": request.creator_id}).sort("_id", -1).limit(5).to_list(5)
    sources = await db.sources.find({"creator_id": request.creator_id}).sort("_id", -1).limit(5).to_list(5)
    memory = await db.learning_memory.find_one({"creator_id": request.creator_id}) or {"learnings": []}

    context = "\n".join([f"{s.get('title')}: {s.get('content', '')[:700]}" for s in sources])
    prompt = SCRIPT_SYSTEM_PROMPT.format(max_duration_seconds=request.max_duration_seconds) + f"""
Profile: {profile}
Last videos: {videos}
Learned strategy: {memory.get('learnings', [])}
Source context: {context}
Generate script for topic={request.topic}, goal={request.goal}, audience={request.audience}, vibe={request.vibe}, platform={request.platform}, source_hint={request.source_hint}
"""

    llm = GeminiService()
    script = await llm.generate(prompt)
    critic = await llm.generate(CRITIC_PROMPT + "\n\n" + script)

    return {
        "title": f"Script: {request.topic}",
        "estimated_duration_seconds": min(request.max_duration_seconds, 175),
        "script": script,
        "critic_feedback": critic,
        "improvement_memory_used": memory.get("learnings", []),
    }
