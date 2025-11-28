from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
from uuid import uuid4
import json


class Meeting(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    title: str
    status: str = "pending"          # pending | processing | done | error
    source_type: str = "upload"      # upload | youtube | zoom
    source_url: Optional[str] = None
    file_path: Optional[str] = None
    file_name: Optional[str] = None
    duration_seconds: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    # Results — stored as serialised JSON strings
    transcript: Optional[str] = None        # full text
    speakers_json: Optional[str] = None     # list[{speaker, text, start, end}]
    summary: Optional[str] = None           # bullet-point summary text
    action_items_json: Optional[str] = None # list[str]
    chapters_json: Optional[str] = None     # list[{title, summary, start}]
    keywords_json: Optional[str] = None     # list[str]

    error_message: Optional[str] = None

    # ── helpers ───────────────────────────────────────────────────
    def set_speakers(self, data: list):
        self.speakers_json = json.dumps(data)

    def get_speakers(self) -> list:
        return json.loads(self.speakers_json) if self.speakers_json else []

    def set_action_items(self, data: list):
        self.action_items_json = json.dumps(data)

    def get_action_items(self) -> list:
        return json.loads(self.action_items_json) if self.action_items_json else []

    def set_chapters(self, data: list):
        self.chapters_json = json.dumps(data)

    def get_chapters(self) -> list:
        return json.loads(self.chapters_json) if self.chapters_json else []

    def set_keywords(self, data: list):
        self.keywords_json = json.dumps(data)

    def get_keywords(self) -> list:
        return json.loads(self.keywords_json) if self.keywords_json else []


class MeetingPublic(SQLModel):
    """Serialisable response model (no raw JSON strings)."""
    id: str
    title: str
    status: str
    source_type: str
    source_url: Optional[str]
    file_name: Optional[str]
    duration_seconds: Optional[int]
    created_at: datetime
    completed_at: Optional[datetime]
    transcript: Optional[str]
    speakers: Optional[list] = None
    summary: Optional[str]
    action_items: Optional[list] = None
    chapters: Optional[list] = None
    keywords: Optional[list] = None
    error_message: Optional[str]

    @classmethod
    def from_meeting(cls, m: Meeting) -> "MeetingPublic":
        return cls(
            id=m.id,
            title=m.title,
            status=m.status,
            source_type=m.source_type,
            source_url=m.source_url,
            file_name=m.file_name,
            duration_seconds=m.duration_seconds,
            created_at=m.created_at,
            completed_at=m.completed_at,
            transcript=m.transcript,
            speakers=m.get_speakers(),
            summary=m.summary,
            action_items=m.get_action_items(),
            chapters=m.get_chapters(),
            keywords=m.get_keywords(),
            error_message=m.error_message,
        )
