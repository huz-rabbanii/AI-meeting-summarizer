"""
Transcription service — AssemblyAI primary, OpenAI Whisper fallback.

AssemblyAI gives us out-of-the-box:
  - Speaker diarisation (speaker_labels)
  - Auto chapters / topic segmentation
  - Key-phrase highlights
  - Summarisation bullets

OpenAI Whisper gives us:
  - High-quality transcript (no speaker labels)
  - GPT-4o then extracts everything else
"""

import os
import time
import httpx
from typing import Optional
from openai import OpenAI

ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY", "")
OPENAI_API_KEY     = os.getenv("OPENAI_API_KEY", "")

AAI_BASE   = "https://api.assemblyai.com/v2"
AAI_HEADERS = {"authorization": ASSEMBLYAI_API_KEY}


# ── AssemblyAI path ────────────────────────────────────────────────────────────

def _aai_upload(file_path: str) -> str:
    """Upload file to AssemblyAI CDN and return the upload URL."""
    with open(file_path, "rb") as f:
        resp = httpx.post(
            f"{AAI_BASE}/upload",
            headers={**AAI_HEADERS, "content-type": "application/octet-stream"},
            content=f.read(),
            timeout=120,
        )
    resp.raise_for_status()
    return resp.json()["upload_url"]


def _aai_submit(audio_url: str) -> str:
    """Submit a transcription job and return the transcript ID."""
    payload = {
        "audio_url": audio_url,
        "speaker_labels": True,
        "auto_chapters": True,
        "iab_categories": True,
        "auto_highlights": True,
        "summarization": True,
        "summary_model": "informative",
        "summary_type": "bullets",
        "sentiment_analysis": True,
    }
    resp = httpx.post(
        f"{AAI_BASE}/transcript",
        headers=AAI_HEADERS,
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["id"]


def _aai_poll(transcript_id: str, poll_interval: int = 5) -> dict:
    """Poll until the job completes and return the full transcript object."""
    url = f"{AAI_BASE}/transcript/{transcript_id}"
    while True:
        resp = httpx.get(url, headers=AAI_HEADERS, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if data["status"] == "completed":
            return data
        if data["status"] == "error":
            raise RuntimeError(f"AssemblyAI error: {data.get('error')}")
        time.sleep(poll_interval)


def transcribe_with_assemblyai(file_path: str) -> dict:
    """
    Returns:
    {
        transcript: str,
        speakers: [{speaker, text, start, end}],
        summary: str (bullet points),
        chapters: [{title, summary, start}],
        keywords: [str],
        duration_seconds: int,
    }
    """
    upload_url   = _aai_upload(file_path)
    transcript_id = _aai_submit(upload_url)
    data = _aai_poll(transcript_id)

    # ── Speakers ──────────────────────────────────────────────────
    speakers = []
    if data.get("utterances"):
        for utt in data["utterances"]:
            speakers.append({
                "speaker": f"Speaker {utt['speaker']}",
                "text":    utt["text"],
                "start":   utt["start"],   # ms
                "end":     utt["end"],
            })

    # ── Chapters ──────────────────────────────────────────────────
    chapters = []
    if data.get("chapters"):
        for ch in data["chapters"]:
            chapters.append({
                "title":   ch.get("gist", ch.get("headline", "")),
                "summary": ch.get("summary", ""),
                "start":   ch.get("start", 0),
            })

    # ── Keywords ─────────────────────────────────────────────────
    keywords = []
    if data.get("auto_highlights_result", {}).get("results"):
        keywords = [h["text"] for h in data["auto_highlights_result"]["results"][:20]]

    duration = int((data.get("audio_duration") or 0))

    return {
        "transcript":       data.get("text", ""),
        "speakers":         speakers,
        "summary":          data.get("summary", ""),
        "chapters":         chapters,
        "keywords":         keywords,
        "duration_seconds": duration,
    }


# ── OpenAI Whisper fallback ────────────────────────────────────────────────────

def transcribe_with_whisper(file_path: str) -> dict:
    """
    Uses OpenAI Whisper for transcript, then GPT-4o to extract structure.
    No speaker diarisation (Whisper API doesn't support it).
    """
    client = OpenAI(api_key=OPENAI_API_KEY)

    # Transcribe
    with open(file_path, "rb") as audio:
        whisper_resp = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio,
            response_format="verbose_json",
        )
    transcript_text = whisper_resp.text
    duration = int(getattr(whisper_resp, "duration", 0) or 0)

    # Extract structure via GPT-4o
    gpt_resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a meeting analyst. Given a meeting transcript, return a JSON object with:\n"
                    "- summary: string (3-6 concise bullet points starting with '• ')\n"
                    "- action_items: list of strings (concrete tasks with owner if identifiable)\n"
                    "- chapters: list of {title: str, summary: str} topic segments\n"
                    "- keywords: list of up to 15 key terms or names\n"
                    "Return only valid JSON."
                ),
            },
            {"role": "user", "content": f"TRANSCRIPT:\n{transcript_text}"},
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
    )

    import json
    structured = json.loads(gpt_resp.choices[0].message.content)

    return {
        "transcript":       transcript_text,
        "speakers":         [],   # not available without diarisation
        "summary":          structured.get("summary", ""),
        "action_items":     structured.get("action_items", []),
        "chapters":         structured.get("chapters", []),
        "keywords":         structured.get("keywords", []),
        "duration_seconds": duration,
    }


# ── Public entry point ─────────────────────────────────────────────────────────

def transcribe(file_path: str) -> dict:
    """
    Attempt AssemblyAI first (richer output). Fall back to Whisper if no key.
    After transcription, always run GPT action-item extraction if not already done.
    """
    if ASSEMBLYAI_API_KEY:
        result = transcribe_with_assemblyai(file_path)
        # AssemblyAI doesn't extract action items — run GPT on top
        if not result.get("action_items"):
            result["action_items"] = _extract_action_items(result["transcript"])
        return result
    elif OPENAI_API_KEY:
        return transcribe_with_whisper(file_path)
    else:
        raise RuntimeError("Set ASSEMBLYAI_API_KEY or OPENAI_API_KEY in .env")


def _extract_action_items(transcript: str) -> list[str]:
    if not OPENAI_API_KEY or not transcript:
        return []
    client = OpenAI(api_key=OPENAI_API_KEY)
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "Extract all action items from the meeting transcript. "
                    "Return a JSON object with key 'action_items': list of strings. "
                    "Each item should be specific and actionable. Include owner if mentioned."
                ),
            },
            {"role": "user", "content": transcript},
        ],
        response_format={"type": "json_object"},
        temperature=0.1,
    )
    import json
    data = json.loads(resp.choices[0].message.content)
    return data.get("action_items", [])
