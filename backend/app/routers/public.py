from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/public", tags=["public"])


@router.get("/snippets/{slug}", response_model=schemas.PublicSnippetOut)
def get_public_snippet(slug: str, db: Session = Depends(get_db)):
    snippet = db.query(models.Snippet).filter(
        models.Snippet.share_slug == slug,
        models.Snippet.is_public == True,
    ).first()
    if not snippet:
        raise HTTPException(status_code=404, detail="Snippet not found or not public")
    return snippet