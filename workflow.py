from fastapi import APIRouter
from app.core.db import get_db
from app.schemas.common import CreatorProfile, VideoPerformance, SourceText, ScriptRequest
from app.agents.workflow import CreatorPilotWorkflow

router = APIRouter(prefix="/api")


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
    result = await db.videos.insert_one(video.model_dump())
    return {"ok": True, "id": str(result.inserted_id)}


@router.post("/sources/text")
async def add_source(source: SourceText):
    db = get_db()
    result = await db.sources.insert_one(source.model_dump())
    return {"ok": True, "id": str(result.inserted_id)}


@router.post("/scripts/generate")
async def generate_script(request: ScriptRequest):
    workflow = CreatorPilotWorkflow()
    return await workflow.generate_script(request)


@router.post("/learning/update/{creator_id}")
async def update_learning(creator_id: str):
    db = get_db()
    videos = await db.videos.find({"creator_id": creator_id}).sort("_id", -1).limit(20).to_list(20)
    learnings = []
    if videos:
        top = sorted(videos, key=lambda v: (v.get("likes", 0) + 2*v.get("comments", 0) + 3*v.get("shares", 0) + 4*v.get("follows", 0)) / max(v.get("views", 1), 1), reverse=True)[:3]
        for video in top:
            learnings.append(f"High performer: topic='{video.get('topic')}', hook='{video.get('hook_type')}', tone='{video.get('tone')}'. Prefer similar patterns when relevant.")
    await db.learning_memory.update_one({"creator_id": creator_id}, {"$set": {"creator_id": creator_id, "learnings": learnings}}, upsert=True)
    return {"ok": True, "learnings": learnings}
