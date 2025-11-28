import os
import shutil
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from sqlmodel import Session, select

from database import get_session
from models import Meeting, MeetingPublic
from services.transcription import transcribe
from services.youtube import download_youtube_audio
from services.pdf_export import export_pdf
from services.email_service import send_summary_email

router = APIRouter()

ALLOWED_AUDIO_VIDEO = {
    "audio/mpeg", "audio/mp3", "audio/wav", "audio/ogg", "audio/flac",
    "audio/x-m4a", "audio/mp4", "video/mp4", "video/webm",
    "video/quicktime", "application/octet-stream",
}
MAX_FILE_MB = 500


# ── Background processing ──────────────────────────────────────────────────────

def _process_meeting(meeting_id: str, file_path: str, db_url: str):
    """Run in a background thread: transcribe → store results."""
    from sqlmodel import create_engine, Session as SyncSession
    engine = create_engine(db_url, connect_args={"check_same_thread": False})

    with SyncSession(engine) as session:
        meeting = session.get(Meeting, meeting_id)
        if not meeting:
            return
        meeting.status = "processing"
        session.add(meeting)
        session.commit()

        try:
            result = transcribe(file_path)
            meeting.transcript       = result.get("transcript", "")
            meeting.summary          = result.get("summary", "")
            meeting.duration_seconds = result.get("duration_seconds")
            meeting.set_speakers(result.get("speakers", []))
            meeting.set_action_items(result.get("action_items", []))
            meeting.set_chapters(result.get("chapters", []))
            meeting.set_keywords(result.get("keywords", []))
            meeting.status           = "done"
            meeting.completed_at     = datetime.utcnow()
        except Exception as exc:
            meeting.status        = "error"
            meeting.error_message = str(exc)

        session.add(meeting)
        session.commit()


# ── Routes ─────────────────────────────────────────────────────────────────────

@router.get("/", response_model=list[MeetingPublic])
def list_meetings(session: Session = Depends(get_session)):
    meetings = session.exec(select(Meeting).order_by(Meeting.created_at.desc())).all()
    return [MeetingPublic.from_meeting(m) for m in meetings]


@router.get("/{meeting_id}", response_model=MeetingPublic)
def get_meeting(meeting_id: str, session: Session = Depends(get_session)):
    m = session.get(Meeting, meeting_id)
    if not m:
        raise HTTPException(404, "Meeting not found")
    return MeetingPublic.from_meeting(m)


@router.post("/upload", response_model=MeetingPublic, status_code=202)
async def upload_meeting(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    session: Session = Depends(get_session),
):
    # Validate size
    contents = await file.read()
    if len(contents) > MAX_FILE_MB * 1024 * 1024:
        raise HTTPException(413, f"File exceeds {MAX_FILE_MB} MB limit")

    # Save to disk
    file_id  = str(uuid.uuid4())
    ext      = os.path.splitext(file.filename or "audio.mp3")[1] or ".mp3"
    file_path = os.path.join("uploads", f"{file_id}{ext}")
    with open(file_path, "wb") as f:
        f.write(contents)

    meeting = Meeting(
        id=file_id,
        title=title or (file.filename or "Untitled Meeting"),
        source_type="upload",
        file_path=file_path,
        file_name=file.filename,
    )
    session.add(meeting)
    session.commit()
    session.refresh(meeting)

    from database import DATABASE_URL
    background_tasks.add_task(_process_meeting, meeting.id, file_path, DATABASE_URL)
    return MeetingPublic.from_meeting(meeting)


@router.post("/youtube", response_model=MeetingPublic, status_code=202)
async def process_youtube(
    background_tasks: BackgroundTasks,
    url: str = Form(...),
    title: Optional[str] = Form(None),
    session: Session = Depends(get_session),
):
    meeting_id = str(uuid.uuid4())
    meeting = Meeting(
        id=meeting_id,
        title=title or "YouTube Meeting",
        source_type="youtube",
        source_url=url,
        status="pending",
    )
    session.add(meeting)
    session.commit()
    session.refresh(meeting)

    def _download_and_process(mid: str, yt_url: str):
        from sqlmodel import create_engine, Session as S
        from database import DATABASE_URL
        eng = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
        with S(eng) as s:
            m = s.get(Meeting, mid)
            if not m:
                return
            m.status = "processing"
            s.add(m); s.commit()
            try:
                file_path, yt_title = download_youtube_audio(yt_url)
                if not m.title or m.title == "YouTube Meeting":
                    m.title = yt_title
                m.file_path = file_path
                s.add(m); s.commit()
            except Exception as exc:
                m.status = "error"; m.error_message = str(exc)
                s.add(m); s.commit(); return
        _process_meeting(mid, file_path, DATABASE_URL)

    background_tasks.add_task(_download_and_process, meeting.id, url)
    return MeetingPublic.from_meeting(meeting)


@router.delete("/{meeting_id}", status_code=204)
def delete_meeting(meeting_id: str, session: Session = Depends(get_session)):
    m = session.get(Meeting, meeting_id)
    if not m:
        raise HTTPException(404, "Meeting not found")
    if m.file_path and os.path.exists(m.file_path):
        os.remove(m.file_path)
    session.delete(m)
    session.commit()


@router.get("/{meeting_id}/export/pdf")
def export_meeting_pdf(meeting_id: str, session: Session = Depends(get_session)):
    m = session.get(Meeting, meeting_id)
    if not m:
        raise HTTPException(404, "Meeting not found")
    if m.status != "done":
        raise HTTPException(400, "Meeting processing not complete")

    data = MeetingPublic.from_meeting(m).model_dump()
    pdf_bytes = export_pdf(data)
    safe_title = "".join(c if c.isalnum() or c in " _-" else "_" for c in m.title)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{safe_title}.pdf"'},
    )


@router.post("/{meeting_id}/email")
def email_meeting(
    meeting_id: str,
    recipients: list[str],
    attach_pdf: bool = True,
    session: Session = Depends(get_session),
):
    m = session.get(Meeting, meeting_id)
    if not m:
        raise HTTPException(404, "Meeting not found")
    if m.status != "done":
        raise HTTPException(400, "Meeting processing not complete")

    data = MeetingPublic.from_meeting(m).model_dump()
    pdf_bytes = export_pdf(data) if attach_pdf else None

    try:
        send_summary_email(recipients, data, pdf_bytes)
    except RuntimeError as exc:
        raise HTTPException(500, str(exc))

    return {"sent_to": recipients}
