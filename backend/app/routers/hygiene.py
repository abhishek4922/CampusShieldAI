"""
CampusShield AI — Digital Hygiene Router

Endpoints:
  GET  /v1/hygiene/lessons          - Get available lessons for user
  POST /v1/hygiene/lessons/{id}/complete - Mark lesson complete with score
  GET  /v1/hygiene/progress         - Get user's hygiene score & streaks
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel, Field

from app.database import get_db
from app.models import User, HygieneSession
from app.dependencies import get_current_user

router = APIRouter()

# Lesson catalogue (production: load from DB/config)
LESSON_CATALOGUE = [
    {"id": "phishing-basics", "title": "Recognising Phishing Emails", "difficulty": "beginner", "xp": 10},
    {"id": "url-safety", "title": "Spotting Dangerous Links", "difficulty": "beginner", "xp": 10},
    {"id": "social-engineering", "title": "Social Engineering Tactics", "difficulty": "intermediate", "xp": 20},
    {"id": "password-hygiene", "title": "Password Best Practices", "difficulty": "beginner", "xp": 10},
    {"id": "mfa-guide", "title": "Multi-Factor Authentication", "difficulty": "intermediate", "xp": 20},
    {"id": "data-privacy", "title": "Protecting Your Personal Data", "difficulty": "intermediate", "xp": 20},
    {"id": "advanced-threats", "title": "Advanced Persistent Threats", "difficulty": "advanced", "xp": 50},
]


class LessonCompleteRequest(BaseModel):
    score: int = Field(..., ge=0, le=100)


class ProgressResponse(BaseModel):
    hygiene_score:     int
    lessons_completed: int
    lessons_total:     int
    completion_pct:    float
    rank:              str


def _rank(score: int) -> str:
    if score < 50:  return "Beginner 🌱"
    if score < 150: return "Defender 🛡️"
    if score < 300: return "Guardian 🔒"
    return "CyberSentinel 🚀"


@router.get("/lessons")
async def get_lessons(current_user: User = Depends(get_current_user)) -> List[dict]:
    """Return the lesson catalogue (adaptive difficulty based on hygiene score)."""
    user_score = current_user.hygiene_score
    # Filter out advanced lessons until user has enough score
    return [
        l for l in LESSON_CATALOGUE
        if not (l["difficulty"] == "advanced" and user_score < 100)
    ]


@router.post("/lessons/{lesson_id}/complete")
async def complete_lesson(
    lesson_id: str,
    payload: LessonCompleteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Record lesson completion and award XP to hygiene score."""
    lesson = next((l for l in LESSON_CATALOGUE if l["id"] == lesson_id), None)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    # Check if already completed
    existing = await db.execute(
        select(HygieneSession).where(
            HygieneSession.user_id == current_user.id,
            HygieneSession.lesson_id == lesson_id,
            HygieneSession.completed == True,
        )
    )
    if existing.scalar_one_or_none():
        return {"message": "Already completed", "hygiene_score": current_user.hygiene_score}

    session = HygieneSession(
        campus_id    = current_user.campus_id,
        user_id      = current_user.id,
        lesson_id    = lesson_id,
        completed    = True,
        score        = payload.score,
        difficulty   = lesson["difficulty"],
        completed_at = datetime.now(timezone.utc),
    )
    db.add(session)

    # Award XP proportional to score
    xp_earned = int(lesson["xp"] * (payload.score / 100))
    current_user.hygiene_score = current_user.hygiene_score + xp_earned
    await db.commit()

    return {"message": "Lesson completed!", "xp_earned": xp_earned, "hygiene_score": current_user.hygiene_score, "rank": _rank(current_user.hygiene_score)}


@router.get("/progress", response_model=ProgressResponse)
async def get_progress(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProgressResponse:
    """User's gamified hygiene progress summary."""
    completed_count = await db.execute(
        select(func.count(HygieneSession.id)).where(
            HygieneSession.user_id == current_user.id,
            HygieneSession.completed == True,
        )
    )
    completed = completed_count.scalar_one() or 0

    return ProgressResponse(
        hygiene_score     = current_user.hygiene_score,
        lessons_completed = completed,
        lessons_total     = len(LESSON_CATALOGUE),
        completion_pct    = round((completed / len(LESSON_CATALOGUE)) * 100, 1),
        rank              = _rank(current_user.hygiene_score),
    )
