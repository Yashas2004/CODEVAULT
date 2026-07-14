import json
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import or_, text
from .. import models, schemas, auth
from ..database import get_db
from ..redis_client import redis_client
from fastapi import HTTPException
from ..rate_limit import rate_limiter

router = APIRouter(prefix="/snippets", tags=["snippets"])


def get_cache_version(user_id: int) -> int:
    """Get current cache version for a user. Defaults to 0 if not set."""
    version = redis_client.get(f"snippets:version:{user_id}")
    return int(version) if version else 0


def bump_cache_version(user_id: int):
    """Invalidate ALL cached snippet lists for this user in O(1),
    regardless of what search query they were cached under."""
    redis_client.incr(f"snippets:version:{user_id}")


@router.post("/", response_model=schemas.SnippetOut,
             dependencies=[Depends(rate_limiter(30, 60))])
def create_snippet(snippet: schemas.SnippetCreate, db: Session = Depends(get_db),
                    user: models.User = Depends(auth.get_current_user)):
    new_snippet = models.Snippet(**snippet.dict(), owner_id=user.id)
    db.add(new_snippet); db.commit(); db.refresh(new_snippet)
    bump_cache_version(user.id)
    return new_snippet

@router.put("/{snippet_id}", response_model=schemas.SnippetOut)
def update_snippet(snippet_id: int, snippet: schemas.SnippetCreate,
                    db: Session = Depends(get_db),
                    user: models.User = Depends(auth.get_current_user)):
    existing = db.query(models.Snippet).filter(
        models.Snippet.id == snippet_id,
        models.Snippet.owner_id == user.id
    ).first()
    if not existing:
        raise HTTPException(status_code=404, detail="Snippet not found")

    existing.title = snippet.title
    existing.language = snippet.language
    existing.code = snippet.code
    existing.tags = snippet.tags
    db.commit()
    db.refresh(existing)
    bump_cache_version(user.id)
    return existing

@router.get("/", response_model=schemas.PaginatedSnippets)
def list_snippets(q: str = "", cursor: int | None = None, limit: int = 20,
                   db: Session = Depends(get_db),
                   user: models.User = Depends(auth.get_current_user)):
    limit = min(limit, 50)  # hard cap so nobody can request 10,000 rows at once

    version = get_cache_version(user.id)
    cache_key = f"snippets:{user.id}:v{version}:{q}:{cursor}:{limit}"
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    query = db.query(models.Snippet).filter(models.Snippet.owner_id == user.id)
    if q:
        query = query.filter(
            text("search_vector @@ plainto_tsquery('english', :q)")
        ).params(q=q)

    if cursor is not None:
        query = query.filter(models.Snippet.id < cursor)
    
    

    # order newest-first, fetch one extra row to check if there's more
    results = query.order_by(models.Snippet.id.desc()).limit(limit + 1).all()

    has_more = len(results) > limit
    results = results[:limit]
    next_cursor = results[-1].id if results and has_more else None

    out = {
        "items": [schemas.SnippetOut.from_orm(r).dict() for r in results],
        "next_cursor": next_cursor,
        "has_more": has_more,
    }
    redis_client.setex(cache_key, 60, json.dumps(out, default=str))
    return out


@router.delete("/{snippet_id}")
def delete_snippet(snippet_id: int, db: Session = Depends(get_db),
                    user: models.User = Depends(auth.get_current_user)):
    snippet = db.query(models.Snippet).filter(
        models.Snippet.id == snippet_id,
        models.Snippet.owner_id == user.id
    ).first()
    if not snippet:
        raise HTTPException(status_code=404, detail="Snippet not found")
    db.delete(snippet)
    db.commit()
    bump_cache_version(user.id)
    return {"detail": "Deleted"}