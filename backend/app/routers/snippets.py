import json
from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
from sqlalchemy import text
from .. import models, schemas, auth
from ..database import get_db
from ..redis_client import get_redis
from fastapi import HTTPException
from ..rate_limit import rate_limiter
from ..models import generate_share_slug

router = APIRouter(prefix="/snippets", tags=["snippets"])

IDEMPOTENCY_TTL_SECONDS = 60 * 60 * 24  # 24 hours


def get_cache_version(redis_conn, user_id: int) -> int:
    version = redis_conn.get(f"snippets:version:{user_id}")
    return int(version) if version else 0


def bump_cache_version(redis_conn, user_id: int):
    redis_conn.incr(f"snippets:version:{user_id}")


@router.post("/", response_model=schemas.SnippetOut,
             dependencies=[Depends(rate_limiter(30, 60))])
def create_snippet(snippet: schemas.SnippetCreate, db: Session = Depends(get_db),
                    user: models.User = Depends(auth.get_current_user),
                    redis_conn=Depends(get_redis),
                    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")):

    cache_key = None
    if idempotency_key:
        cache_key = f"idempotency:{user.id}:{idempotency_key}"
        cached = redis_conn.get(cache_key)
        if cached and cached != "PENDING":
            return json.loads(cached)

        reserved = redis_conn.set(cache_key, "PENDING", nx=True, ex=IDEMPOTENCY_TTL_SECONDS)
        if not reserved:
            raise HTTPException(
                status_code=409,
                detail="Duplicate request already in progress, please retry shortly"
            )

    try:
        new_snippet = models.Snippet(**snippet.dict(), owner_id=user.id)
        db.add(new_snippet); db.commit(); db.refresh(new_snippet)
        bump_cache_version(redis_conn, user.id)

        result = schemas.SnippetOut.from_orm(new_snippet).dict()

        if cache_key:
            redis_conn.setex(cache_key, IDEMPOTENCY_TTL_SECONDS, json.dumps(result, default=str))

        return result
    except Exception:
        if cache_key:
            redis_conn.delete(cache_key)
        raise


@router.put("/{snippet_id}", response_model=schemas.SnippetOut)
def update_snippet(snippet_id: int, snippet: schemas.SnippetCreate,
                    db: Session = Depends(get_db),
                    user: models.User = Depends(auth.get_current_user),
                    redis_conn=Depends(get_redis)):
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
    bump_cache_version(redis_conn, user.id)
    return existing


@router.post("/{snippet_id}/share", response_model=schemas.ShareResponse)
def create_share_link(snippet_id: int, db: Session = Depends(get_db),
                       user: models.User = Depends(auth.get_current_user)):
    snippet = db.query(models.Snippet).filter(
        models.Snippet.id == snippet_id,
        models.Snippet.owner_id == user.id
    ).first()
    if not snippet:
        raise HTTPException(status_code=404, detail="Snippet not found")

    if not snippet.share_slug:
        snippet.share_slug = generate_share_slug()
    snippet.is_public = True
    db.commit()
    db.refresh(snippet)
    return snippet


@router.delete("/{snippet_id}/share", response_model=schemas.ShareResponse)
def revoke_share_link(snippet_id: int, db: Session = Depends(get_db),
                       user: models.User = Depends(auth.get_current_user)):
    snippet = db.query(models.Snippet).filter(
        models.Snippet.id == snippet_id,
        models.Snippet.owner_id == user.id
    ).first()
    if not snippet:
        raise HTTPException(status_code=404, detail="Snippet not found")

    snippet.is_public = False
    db.commit()
    db.refresh(snippet)
    return snippet


@router.get("/", response_model=schemas.PaginatedSnippets)
def list_snippets(q: str = "", cursor: int | None = None, limit: int = 20,
                   db: Session = Depends(get_db),
                   user: models.User = Depends(auth.get_current_user),
                   redis_conn=Depends(get_redis)):
    limit = min(limit, 50)

    version = get_cache_version(redis_conn, user.id)
    cache_key = f"snippets:{user.id}:v{version}:{q}:{cursor}:{limit}"
    cached = redis_conn.get(cache_key)
    if cached:
        return json.loads(cached)

    query = db.query(models.Snippet).filter(models.Snippet.owner_id == user.id)
    if q:
        query = query.filter(
            text("search_vector @@ plainto_tsquery('english', :q)")
        ).params(q=q)

    if cursor is not None:
        query = query.filter(models.Snippet.id < cursor)

    results = query.order_by(models.Snippet.id.desc()).limit(limit + 1).all()

    has_more = len(results) > limit
    results = results[:limit]
    next_cursor = results[-1].id if results and has_more else None

    items = []
    for r in results:
        item = schemas.SnippetOut.from_orm(r).dict()
        if r.is_public:
            raw_count = redis_conn.get(f"views:{r.id}")
            item["view_count"] = int(raw_count) if raw_count else 0
        items.append(item)

    out = {
        "items": items,
        "next_cursor": next_cursor,
        "has_more": has_more,
    }
    redis_conn.setex(cache_key, 60, json.dumps(out, default=str))
    return out


@router.delete("/{snippet_id}")
def delete_snippet(snippet_id: int, db: Session = Depends(get_db),
                    user: models.User = Depends(auth.get_current_user),
                    redis_conn=Depends(get_redis)):
    snippet = db.query(models.Snippet).filter(
        models.Snippet.id == snippet_id,
        models.Snippet.owner_id == user.id
    ).first()
    if not snippet:
        raise HTTPException(status_code=404, detail="Snippet not found")
    db.delete(snippet)
    db.commit()
    bump_cache_version(redis_conn, user.id)
    return {"detail": "Deleted"}