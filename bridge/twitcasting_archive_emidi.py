from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict
from pathlib import Path
from typing import Any

from voice.features import extract_wav_features

TWITCASTING_API = "https://apiv2.twitcasting.tv"
DEFAULT_SCREEN_ID = "_akareeeen_"


def _json_request(url: str, *, headers: dict[str, str] | None = None) -> dict[str, Any]:
    request = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_keymaster_secret(
    *,
    base_url: str,
    auth_token: str,
    api_name: str = "twitcasting",
    key_names: tuple[str, ...] = ("access_token", "token", "api_key"),
) -> str:
    """Read a TwitCasting token through Keymaster without printing or persisting it."""
    if not base_url or not auth_token:
        raise RuntimeError("KEYMASTER_NOT_CONNECTED")
    headers = {"Authorization": f"Bearer {auth_token}"}
    root = base_url.rstrip("/")
    for key_name in key_names:
        query = urllib.parse.urlencode({"api_name": api_name, "key_name": key_name})
        try:
            body = _json_request(f"{root}/vault/api-key?{query}", headers=headers)
        except urllib.error.HTTPError:
            continue
        value = body.get("api_key")
        if value:
            return str(value)
    raise RuntimeError("TWITCASTING_KEYMASTER_SECRET_EMPTY")


def list_movies(*, access_token: str, screen_id: str, limit: int = 50, max_movies: int = 200) -> list[dict[str, Any]]:
    """List archived movie metadata through TwitCasting API v2."""
    headers = {
        "Accept": "application/json",
        "X-Api-Version": "2.0",
        "Authorization": f"Bearer {access_token}",
    }
    movies: list[dict[str, Any]] = []
    slice_id: str | None = None
    while len(movies) < max_movies:
        params: dict[str, str] = {"limit": str(min(limit, max_movies - len(movies)))}
        if slice_id:
            params["slice_id"] = slice_id
        url = f"{TWITCASTING_API}/users/{urllib.parse.quote(screen_id)}/movies?{urllib.parse.urlencode(params)}"
        body = _json_request(url, headers=headers)
        batch = list(body.get("movies") or [])
        if not batch:
            break
        movies.extend(batch)
        last_id = str(batch[-1].get("id") or "")
        if not last_id or len(batch) < int(params["limit"]):
            break
        slice_id = last_id
    return movies[:max_movies]


def analyzable_movies(movies: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [movie for movie in movies if bool(movie.get("is_recorded")) and bool(movie.get("hls_url"))]


def _segment_hls_to_pcm_wav(*, hls_url: str, output_dir: Path, segment_seconds: int) -> list[Path]:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("FFMPEG_NOT_AVAILABLE")
    pattern = output_dir / "segment-%05d.wav"
    command = [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        hls_url,
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-c:a",
        "pcm_s16le",
        "-f",
        "segment",
        "-segment_time",
        str(segment_seconds),
        "-reset_timestamps",
        "1",
        str(pattern),
    ]
    subprocess.run(command, check=True, timeout=60 * 60)
    return sorted(output_dir.glob("segment-*.wav"))


def build_voice_event(*, movie: dict[str, Any], segment_index: int, segment_seconds: int, wav_bytes: bytes) -> dict[str, Any]:
    features = extract_wav_features(wav_bytes)
    return {
        "schema_version": 1,
        "type": "voice_event",
        "source": "twitcasting",
        "source_id": DEFAULT_SCREEN_ID,
        "movie": {
            "id": str(movie.get("id") or ""),
            "title": str(movie.get("title") or ""),
            "link": str(movie.get("link") or ""),
            "created": movie.get("created"),
            "duration": movie.get("duration"),
        },
        "segment": {
            "index": segment_index,
            "offset_seconds": segment_index * segment_seconds,
            "target_seconds": segment_seconds,
        },
        "emotion_midi": {
            "valence": features.valence,
            "arousal": features.arousal,
            "tension": features.tension,
            "velocity": features.velocity,
            "valence_source": features.valence_source,
            "confidence": features.confidence,
        },
        "acoustic_features": asdict(features),
        "truth_boundary": {
            "raw_audio_persisted": False,
            "transcript_present": False,
            "valence_semantics_inferred": False,
            "note": "VOICE-1 acoustic features only. Transcript/semantic valence is a separate later layer.",
        },
        "privacy": "private-derived",
    }


def analyze_movie(*, movie: dict[str, Any], segment_seconds: int = 300) -> list[dict[str, Any]]:
    hls_url = str(movie.get("hls_url") or "")
    if not hls_url:
        raise ValueError("movie has no hls_url")
    events: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="akari-twitcasting-") as temp:
        paths = _segment_hls_to_pcm_wav(hls_url=hls_url, output_dir=Path(temp), segment_seconds=segment_seconds)
        for index, path in enumerate(paths):
            events.append(
                build_voice_event(
                    movie=movie,
                    segment_index=index,
                    segment_seconds=segment_seconds,
                    wav_bytes=path.read_bytes(),
                )
            )
    return events


def main() -> int:
    parser = argparse.ArgumentParser(description="TwitCasting archive -> existing VOICE-1 E-MIDI bridge")
    parser.add_argument("--screen-id", default=DEFAULT_SCREEN_ID)
    parser.add_argument("--max-movies", type=int, default=50)
    parser.add_argument("--movie-id")
    parser.add_argument("--segment-seconds", type=int, default=300)
    parser.add_argument("--metadata-only", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args()

    token = fetch_keymaster_secret(
        base_url=os.getenv("KEYMASTER_BASE_URL", ""),
        auth_token=os.getenv("KEYMASTER_AUTH_TOKEN", ""),
    )
    movies = list_movies(access_token=token, screen_id=args.screen_id, max_movies=args.max_movies)
    available = analyzable_movies(movies)

    if args.metadata_only:
        result: dict[str, Any] = {
            "schema_version": 1,
            "screen_id": args.screen_id,
            "movie_count": len(movies),
            "analyzable_count": len(available),
            "movies": [
                {
                    "id": str(movie.get("id") or ""),
                    "title": str(movie.get("title") or ""),
                    "created": movie.get("created"),
                    "duration": movie.get("duration"),
                    "link": movie.get("link"),
                    "is_recorded": bool(movie.get("is_recorded")),
                    "has_hls": bool(movie.get("hls_url")),
                }
                for movie in movies
            ],
        }
    else:
        selected = available
        if args.movie_id:
            selected = [movie for movie in available if str(movie.get("id")) == args.movie_id]
        if not selected:
            raise RuntimeError("NO_ANALYZABLE_TWITCASTING_MOVIES")
        events: list[dict[str, Any]] = []
        for movie in selected:
            events.extend(analyze_movie(movie=movie, segment_seconds=max(30, args.segment_seconds)))
        result = {
            "schema_version": 1,
            "screen_id": args.screen_id,
            "voice_event_count": len(events),
            "events": events,
            "raw_audio_persisted": False,
        }

    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rendered + "\n", encoding="utf-8")
        print(json.dumps({"output": str(path), "movie_count": len(movies), "analyzable_count": len(available)}, ensure_ascii=False))
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
