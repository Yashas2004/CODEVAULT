from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import get_db
from ..redis_client import get_redis

router = APIRouter(prefix="/public", tags=["public"])


@router.get("/snippets/{slug}", response_model=schemas.PublicSnippetOut)
def get_public_snippet(slug: str, db: Session = Depends(get_db), redis_conn=Depends(get_redis)):
    snippet = db.query(models.Snippet).filter(
        models.Snippet.share_slug == slug,
        models.Snippet.is_public == True,
    ).first()
    if not snippet:
        raise HTTPException(status_code=404, detail="Snippet not found or not public")

    redis_conn.incr(f"views:{snippet.id}")
    return snippet