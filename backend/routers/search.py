from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from database import get_session
from models import Meeting, MeetingPublic

router = APIRouter()


@router.get("/")
def search_meetings(q: str, session: Session = Depends(get_session)):
    """
    Full-text search across transcript, summary, action items, and title.
    SQLite LIKE-based — replace with FTS5 or Elasticsearch for scale.
    """
    if not q or len(q.strip()) < 2:
        return {"query": q, "results": []}

    term = f"%{q.strip()}%"
    meetings = session.exec(
        select(Meeting).where(
            Meeting.status == "done"
        )
    ).all()

    results = []
    for m in meetings:
        hit_fields = []
        if m.title and term.strip("%").lower() in m.title.lower():
            hit_fields.append("title")
        if m.transcript and term.strip("%").lower() in m.transcript.lower():
            hit_fields.append("transcript")
        if m.summary and term.strip("%").lower() in m.summary.lower():
            hit_fields.append("summary")
        if m.action_items_json and term.strip("%").lower() in m.action_items_json.lower():
            hit_fields.append("action_items")

        if hit_fields:
            # Return snippet from transcript if hit there
            snippet = ""
            if "transcript" in hit_fields and m.transcript:
                idx = m.transcript.lower().find(q.strip().lower())
                if idx >= 0:
                    start = max(0, idx - 80)
                    end   = min(len(m.transcript), idx + 160)
                    snippet = "..." + m.transcript[start:end] + "..."

            results.append({
                "id":         m.id,
                "title":      m.title,
                "created_at": m.created_at,
                "hit_fields": hit_fields,
                "snippet":    snippet,
            })

    return {"query": q, "results": results}
