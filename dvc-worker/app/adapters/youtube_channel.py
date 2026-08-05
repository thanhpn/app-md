"""adapter_key = 'youtube_channel' — lists recent videos from a channel/
playlist via yt-dlp (metadata only, no video download) and fetches each
video's transcript via youtube-transcript-api. A new channel is just a
Source row with a different `channel_url`; no code change needed.

Expected Source.config shape:
{
  "channel_url": "https://www.youtube.com/@somechannel/videos",
  "max_items": 20,
  "languages": ["vi", "en"]   # transcript language preference order
}
"""

import asyncio

import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import CouldNotRetrieveTranscript

from app.adapters.base import Adapter, AdapterResult, FetchedPage, ParsedContent, register


def _list_videos(channel_url: str, max_items: int) -> list[dict]:
    opts = {
        "extract_flat": "in_playlist",
        "playlistend": max_items,
        "quiet": True,
        "no_warnings": True,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(channel_url, download=False)
    entries = info.get("entries") or []
    return [e for e in entries if e and e.get("id")]


def _fetch_transcript(video_id: str, languages: list[str]) -> str | None:
    try:
        transcript = YouTubeTranscriptApi().fetch(video_id, languages=languages)
    except CouldNotRetrieveTranscript:
        return None
    except Exception:  # noqa: BLE001 — transcripts are best-effort, never fatal
        return None
    return " ".join(snippet.text for snippet in transcript if snippet.text)


@register("youtube_channel")
class YoutubeChannelAdapter(Adapter):
    async def run(self) -> AdapterResult:
        channel_url = self.config.get("channel_url")
        if not channel_url:
            return AdapterResult(pages=[], errors=["config.channel_url is required"])

        max_items = int(self.config.get("max_items", 20))
        languages = self.config.get("languages", ["vi", "en"])
        errors: list[str] = []

        try:
            videos = await asyncio.to_thread(_list_videos, channel_url, max_items)
        except Exception as exc:  # noqa: BLE001 — channel-list failure must not crash the run
            return AdapterResult(pages=[], errors=[f"channel list failed: {exc}"])

        if not videos:
            # yt-dlp returning 0 entries is almost always a wrong channel_url
            # (needs the exact /videos tab URL) or a layout it can't parse —
            # surfaced as an error so this doesn't read as a silent no-op success.
            return AdapterResult(pages=[], errors=[f"yt-dlp listed 0 videos for {channel_url} — check channel_url is correct"])

        pages: list[FetchedPage] = []
        contents: list[ParsedContent] = []
        for video in videos:
            video_id = video["id"]
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            transcript = await asyncio.to_thread(_fetch_transcript, video_id, languages)
            if not transcript:
                errors.append(f"no transcript for {video_url}")
                continue

            pages.append(FetchedPage(url=video_url, content=transcript))
            contents.append(
                ParsedContent(
                    external_ref=video_id,
                    content_type="youtube_video",
                    body=transcript,
                    title=video.get("title"),
                    author=video.get("uploader") or video.get("channel"),
                )
            )

        return AdapterResult(pages=pages, contents=contents, errors=errors)
