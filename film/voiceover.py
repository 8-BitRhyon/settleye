"""Render a synthetic voiceover for the 3-minute film and mux it.

The storyboard is the source of truth. This script:
1. extracts each scene's `vo` string and start time,
2. cleans pronunciations for TTS,
3. generates one macOS `say` take per scene at a scene-specific pace,
4. places each take at its scene start, and
5. muxes the result onto the silent film without re-encoding video.

Usage:
    cd film
    python3 voiceover.py --voice Samantha
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STORYBOARD = ROOT / "src" / "storyboard.ts"
FILM = ROOT / "out" / "settleye-film-v2-silent.mp4"
OUT_DIR = ROOT / "out" / "vo"
OUTPUT = ROOT / "out" / "settleye-film-v2-preview.mp4"

# Scene-specific pace. The tight beats are the hook and the vision card.
RATES = {
    "hook": 185,
    "pain": 150,
    "extraction": 145,
    "fix": 140,
    "math": 150,
    "vision": 190,
}

PRONUNCIATIONS = {
    "Settleye": "Settle-eye",
    "muse-spark-open": "muse spark open",
    "Pydantic": "pie-dantic",
    "API": "A P I",
    "$2,340": "two thousand three hundred forty dollars",
    "$4,700": "four thousand seven hundred dollars",
    "$4.61": "four dollars and sixty-one cents",
    "$494": "four hundred ninety-four dollars",
    "$128": "one hundred twenty-eight dollars",
    "$99": "ninety-nine dollars",
    "$45": "forty-five dollars",
    "12 of 12": "twelve of twelve",
}


def parse_scenes() -> list[dict]:
    text = STORYBOARD.read_text(encoding="utf-8")
    pattern = re.compile(
        r'id: "(?P<id>[^"]+)",.*?start: (?P<start>\d+),\s+'
        r"duration: (?P<duration>\d+),.*?vo: \"(?P<vo>.*?)\",",
        re.S,
    )
    scenes = []
    for match in pattern.finditer(text):
        scenes.append(
            {
                "id": match.group("id"),
                "start": int(match.group("start")),
                "duration": int(match.group("duration")),
                "vo": match.group("vo"),
            }
        )
    if not scenes:
        raise SystemExit("No scenes parsed from the storyboard.")
    return scenes


def speech_text(text: str) -> str:
    text = text.replace("[name]", "Rhyon")
    text = text.replace("[dates]", "October 26 to November 4, 2026")
    for source, spoken in PRONUNCIATIONS.items():
        text = text.replace(source, spoken)
    return text


def run(command: list[str]) -> None:
    subprocess.run(command, check=True)


def duration(path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=nw=1:nk=1",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return float(result.stdout.strip())


def main() -> None:
    parser = argparse.ArgumentParser(description="Render and mux the film voiceover.")
    parser.add_argument("--voice", default="Samantha")
    parser.add_argument("--film", default=str(FILM))
    parser.add_argument("--output", default=str(OUTPUT))
    parser.add_argument(
        "--audio",
        default=None,
        help="Full human voiceover track. Skips synthetic generation and muxes this file.",
    )
    args = parser.parse_args()

    film = Path(args.film)
    output = Path(args.output)
    if not film.exists():
        raise SystemExit(f"Missing silent film: {film}")

    if args.audio:
        audio = Path(args.audio)
        if not audio.exists():
            raise SystemExit(f"Missing voiceover audio: {audio}")
        seconds = duration(film)
        run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(film),
                "-i",
                str(audio),
                "-filter_complex",
                "[1:a]loudnorm=I=-16:TP=-1.5:LRA=11,apad[a]",
                "-map",
                "0:v:0",
                "-map",
                "[a]",
                "-c:v",
                "copy",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                "-t",
                f"{seconds:.3f}",
                "-movflags",
                "+faststart",
                str(output),
            ]
        )
        print(f"wrote {output}")
        print(f"video {seconds:.2f}s  human voiceover muxed")
        return

    scenes = parse_scenes()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    wavs = []
    for index, scene in enumerate(scenes):
        rate = RATES.get(scene["id"], 160)
        text = speech_text(scene["vo"])
        aiff = OUT_DIR / f"{index:02d}-{scene['id']}.aiff"
        wav = OUT_DIR / f"{index:02d}-{scene['id']}.wav"
        run(["say", "-v", args.voice, "-r", str(rate), "-o", str(aiff), text])
        run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(aiff),
                "-af",
                "silenceremove=start_periods=1:start_silence=0.05:start_threshold=-45dB,"
                "areverse,silenceremove=start_periods=1:start_silence=0.05:start_threshold=-45dB,"
                "areverse,loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000",
                "-ac",
                "2",
                "-c:a",
                "pcm_s16le",
                str(wav),
            ]
        )
        length = duration(wav)
        rows.append(
            {
                "scene": scene["id"],
                "start": scene["start"],
                "scene_s": scene["duration"],
                "vo_s": round(length, 2),
                "rate": rate,
                "fits": length <= scene["duration"],
            }
        )
        wavs.append(wav)

    print(json.dumps(rows, indent=2))
    if not all(row["fits"] for row in rows):
        print("WARNING: at least one VO exceeds its scene duration; tighten the rate.")

    inputs = []
    filters = []
    for index, (scene, wav) in enumerate(zip(scenes, wavs)):
        inputs.extend(["-i", str(wav)])
        delay = scene["start"] * 1000
        filters.append(f"[{index}:a]adelay={delay}|{delay}[a{index}]")
    mix_inputs = "".join(f"[a{index}]" for index in range(len(wavs)))
    filters.append(
        f"{mix_inputs}amix=inputs={len(wavs)}:duration=longest:normalize=0,"
        "alimiter=limit=0.95[aout]"
    )
    full_audio = OUT_DIR / "voiceover-full.wav"
    run(
        [
            "ffmpeg",
            "-y",
            *inputs,
            "-filter_complex",
            ";".join(filters),
            "-map",
            "[aout]",
            "-ar",
            "48000",
            "-ac",
            "2",
            "-c:a",
            "pcm_s16le",
            str(full_audio),
        ]
    )

    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(film),
            "-i",
            str(full_audio),
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-t",
            "180",
            str(output),
        ]
    )
    print(f"wrote {output}")
    print(f"video {duration(output):.2f}s  audio {duration(full_audio):.2f}s")


if __name__ == "__main__":
    main()
