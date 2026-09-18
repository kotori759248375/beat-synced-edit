#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
travel_vlog.py — one-command 卡点旅游 Vlog pipeline.

Wraps the upstream stages without changing them:
  music + footage  →  beat_map → clip_tag → plan_edit → render_edit
  optional: vertical_style (--vertical) for Douyin / 抖音 9:16

Defaults (preset presets/travel_vlog.json):
  --beat-stride 2   fewer cuts that breathe (not every beat)
  calm open         lowest-motion clips forced as opening leads
  Chinese-friendly help text

Upstream project: ZiadAbdelkarim/beat-synced-edit (MIT).
This fork adds travel-vlog convenience only.

Usage (Windows / macOS / Linux):
  python travel_vlog.py bgm.mp3 trip_folder/
  python travel_vlog.py bgm.mp3 footage.mp4 --vertical -o out/trip_vlog.mp4
  python -m travel_vlog bgm.mp3 trip_folder/ --beat-stride 3 --full
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

VIDEO_EXTS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v", ".wmv"}
REPO_ROOT = Path(__file__).resolve().parent
DEFAULT_PRESET = REPO_ROOT / "presets" / "travel_vlog.json"


def _die(msg: str, code: int = 1) -> None:
    print(f"Error: {msg}", file=sys.stderr)
    sys.exit(code)


def check_ffmpeg() -> None:
    """Doctor-like gate: refuse long pipeline if ffmpeg is missing."""
    if shutil.which("ffmpeg") is None:
        _die(
            "ffmpeg 未找到 / ffmpeg not found on PATH.\n"
            "  Windows: winget install ffmpeg   或从 https://ffmpeg.org/download.html 安装并加入 PATH\n"
            "  macOS:   brew install ffmpeg\n"
            "  Linux:   sudo apt install ffmpeg   (or your distro equivalent)"
        )
    try:
        subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            check=True,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        _die("ffmpeg is on PATH but failed to run. Reinstall ffmpeg and retry.")


def load_preset(path: Path | None) -> dict:
    p = path or DEFAULT_PRESET
    if not p.is_file():
        return {
            "beat_stride": 2,
            "calm_open_count": 2,
            "full": False,
            "segment": 1,
            "vertical": False,
            "vertical_fit": "squeeze:1500",
            "vertical_grade": "warm",
            "vertical_size": "1080x1920",
            "scene_threshold": 27.0,
        }
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def find_videos(path: Path) -> list[Path]:
    if path.is_file():
        if path.suffix.lower() in VIDEO_EXTS:
            return [path.resolve()]
        _die(f"Not a video file: {path}")
    if not path.is_dir():
        _die(f"Footage path not found: {path}")
    videos: list[Path] = []
    for root, _dirs, files in os.walk(path):
        for name in files:
            if Path(name).suffix.lower() in VIDEO_EXTS:
                videos.append(Path(root, name).resolve())
    videos.sort()
    if not videos:
        _die(f"No video files found under: {path}")
    return videos


def run_stage(cmd: list[str], title: str) -> None:
    print(f"\n=== {title} ===")
    print(">", " ".join(cmd))
    r = subprocess.run(cmd)
    if r.returncode != 0:
        _die(f"Stage failed ({title}), exit {r.returncode}")


def absolutize_clip_sources(clips_path: Path, videos: list[Path]) -> Path:
    """Rewrite clip 'source' fields to absolute paths so render_edit can find them."""
    by_name = {v.name: str(v) for v in videos}
    # Prefer unique basenames; if collision, last write wins (warn)
    if len(by_name) != len(videos):
        print(
            "Warning: duplicate video basenames — prefer unique filenames in the trip folder."
        )

    with open(clips_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if "source_path" in data and data["source_path"]:
        abs_src = str(Path(data["source_path"]).resolve())
        data["source"] = abs_src
        data["source_path"] = abs_src
        for clip in data.get("clips", []):
            clip["source"] = abs_src
    else:
        for clip in data.get("clips", []):
            name = clip.get("source") or ""
            if name in by_name:
                clip["source"] = by_name[name]
            elif name and Path(name).is_file():
                clip["source"] = str(Path(name).resolve())
        if "sources" in data:
            data["sources"] = [by_name.get(s, s) for s in data["sources"]]

    out = clips_path.with_name(clips_path.stem + "_abs.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return out


def pick_calm_lead_ids(clips_path: Path, count: int) -> str | None:
    """Prefer low-motion / low-energy clips as establishing opens."""
    if count <= 0:
        return None
    with open(clips_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    clips = list(data.get("clips") or [])
    if not clips:
        return None
    ranked = sorted(
        clips,
        key=lambda c: (
            float(c.get("motion_score", 1.0)),
            float(c.get("energy", 1.0)),
            int(c.get("id", 0)),
        ),
    )
    # Chronological among calm picks for a natural establishing open
    calm = ranked[: min(count, len(ranked))]
    calm.sort(key=lambda c: float(c.get("start", 0)))
    ids = [str(c["id"]) for c in calm]
    print(f"Calm open leads (low motion): {','.join(ids)}")
    return ",".join(ids)


def build_parser(preset: dict) -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="travel_vlog",
        description=(
            "卡点旅游 Vlog 一键流水线 / Beat-synced travel vlog one-command pipeline.\n"
            "music + 素材文件夹/文件 → beat_map → clip_tag → plan_edit → render_edit"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例 / Examples:\n"
            "  python travel_vlog.py bgm.mp3 D:\\trip\\clips\\\n"
            "  python travel_vlog.py bgm.mp3 ./trip --vertical -o out/vlog.mp4\n"
            "  python travel_vlog.py bgm.mp3 footage.mp4 --beat-stride 3 --full\n"
            "\n"
            "推荐参数（旅游卡点）: --beat-stride 2（默认，镜头呼吸）; "
            "抖音竖屏加 --vertical; BGM 请自行确认版权，勿假定商用免费。\n"
            "与口播粗剪 jianying-windows-workflow 不同：本工具按鼓点切旅游画面，"
            "不做 ASR / 口头禅删减。详见 docs/TRAVEL_VLOG.md 与 README.zh.md。"
        ),
    )
    p.add_argument(
        "audio",
        nargs="?",
        default=None,
        help="背景音乐路径 / BGM path (mp3, wav, …)",
    )
    p.add_argument(
        "footage",
        nargs="?",
        default=None,
        help="旅游素材：文件夹或单个视频 / Trip folder or one video file",
    )
    p.add_argument(
        "-o",
        "--output",
        default=None,
        help="输出 MP4 路径 / Output MP4 (default: <work>/travel_vlog.mp4)",
    )
    p.add_argument(
        "--work-dir",
        default=None,
        help="中间文件目录 / Working dir for JSON intermediates (default: beside output)",
    )
    p.add_argument(
        "--preset",
        default=str(DEFAULT_PRESET),
        help=f"预设 JSON / Preset JSON (default: {DEFAULT_PRESET.name})",
    )
    p.add_argument(
        "--beat-stride",
        type=int,
        default=None,
        help=(
            f"切密度：1=每拍一切；2+=每隔 N 拍（旅游默认 {preset.get('beat_stride', 2)}，让镜头呼吸）"
            f" / Cut density (travel default {preset.get('beat_stride', 2)})"
        ),
    )
    p.add_argument(
        "--calm-open",
        type=int,
        default=None,
        metavar="N",
        help=(
            f"开场强制使用 N 个低运动建立镜头（默认 {preset.get('calm_open_count', 2)}）"
            f" / Lead with N lowest-motion clips (default {preset.get('calm_open_count', 2)})"
        ),
    )
    p.add_argument(
        "--no-calm-open",
        action="store_true",
        help="关闭冷静开场 / Disable calm establishing open",
    )
    p.add_argument(
        "--full",
        action="store_true",
        default=None,
        help="剪整首歌，而非能量最高片段 / Edit full song instead of best segment",
    )
    p.add_argument(
        "--segment",
        type=int,
        choices=[1, 2, 3],
        default=None,
        help="选用第几个高能片段（1=最佳）/ Which highlight segment (1=best)",
    )
    p.add_argument(
        "--threshold",
        type=float,
        default=None,
        help="场景检测灵敏度（越低越碎，默认 27）/ Scene threshold",
    )
    p.add_argument(
        "--vertical",
        action="store_true",
        default=None,
        help="输出后再转 9:16 竖屏（调用 vertical_style，适合抖音）/ Douyin vertical via vertical_style",
    )
    p.add_argument(
        "--no-vertical",
        action="store_true",
        help="强制不竖屏（覆盖预设）/ Force no vertical pass",
    )
    p.add_argument(
        "--vertical-fit",
        default=None,
        help="竖屏 fit（默认 squeeze:1500）/ vertical_style --fit",
    )
    p.add_argument(
        "--vertical-grade",
        default=None,
        help="竖屏调色（旅游推荐 warm；可选 pink/teal-orange/none…）/ vertical_style --grade",
    )
    p.add_argument(
        "--vertical-size",
        default=None,
        help="竖屏分辨率 WxH（默认 1080x1920）/ vertical size",
    )
    p.add_argument(
        "--thumbs",
        action="store_true",
        help="clip_tag 导出缩略图 / Also export scene thumbnails",
    )
    p.add_argument(
        "--html",
        action="store_true",
        help="各阶段生成 HTML 可视化 / HTML visualizations",
    )
    p.add_argument(
        "--lead",
        default=None,
        help="手动指定开场 clip id（覆盖冷静开场）/ Manual --lead for plan_edit",
    )
    p.add_argument(
        "--exclude",
        default=None,
        help="排除镜头（传给 plan_edit）/ Exclude clips for plan_edit",
    )
    p.add_argument(
        "--pin",
        default=None,
        help="钉住镜头到拍点（传给 plan_edit）/ Pin clips for plan_edit",
    )
    p.add_argument(
        "--skip-render",
        action="store_true",
        help="只做到 EDL，不渲染 / Stop after plan_edit",
    )
    p.add_argument(
        "--doctor",
        action="store_true",
        help="仅检查 ffmpeg / Python 环境后退出 / Check environment and exit",
    )
    return p


def main(argv: list[str] | None = None) -> None:
    # First pass: discover --preset before building full help defaults
    pre = argparse.ArgumentParser(add_help=False)
    pre.add_argument("--preset", default=str(DEFAULT_PRESET))
    pre_args, _ = pre.parse_known_args(argv)
    preset = load_preset(Path(pre_args.preset))

    parser = build_parser(preset)
    args = parser.parse_args(argv)

    check_ffmpeg()
    if args.doctor:
        print("✓ ffmpeg OK")
        print(f"✓ Python {sys.version.split()[0]}")
        print(f"✓ repo root: {REPO_ROOT}")
        print(f"✓ preset: {args.preset}")
        return

    if not args.audio or not args.footage:
        parser.error("audio and footage are required (or pass --doctor)")

    audio = Path(args.audio).expanduser()
    footage = Path(args.footage).expanduser()
    if not audio.is_file():
        _die(f"Audio not found: {audio}")

    videos = find_videos(footage)
    print(f"Footage: {len(videos)} video(s)")

    beat_stride = (
        args.beat_stride
        if args.beat_stride is not None
        else int(preset.get("beat_stride", 2))
    )
    calm_open = 0 if args.no_calm_open else (
        args.calm_open
        if args.calm_open is not None
        else int(preset.get("calm_open_count", 2))
    )
    if args.full is None:
        use_full = bool(preset.get("full", False))
    else:
        use_full = True  # --full was passed
    segment = args.segment if args.segment is not None else int(preset.get("segment", 1))
    threshold = (
        args.threshold
        if args.threshold is not None
        else float(preset.get("scene_threshold", 27.0))
    )
    want_vertical = bool(preset.get("vertical", False))
    if args.vertical:
        want_vertical = True
    if args.no_vertical:
        want_vertical = False
    v_fit = args.vertical_fit or preset.get("vertical_fit", "squeeze:1500")
    v_grade = args.vertical_grade or preset.get("vertical_grade", "warm")
    v_size = args.vertical_size or preset.get("vertical_size", "1080x1920")

    out_mp4 = Path(args.output).expanduser() if args.output else Path("travel_vlog.mp4")
    out_mp4 = out_mp4.resolve()
    work = Path(args.work_dir).expanduser().resolve() if args.work_dir else out_mp4.parent / (out_mp4.stem + "_work")
    work.mkdir(parents=True, exist_ok=True)
    out_mp4.parent.mkdir(parents=True, exist_ok=True)

    py = sys.executable
    beatmap = work / "beatmap.json"
    clips_raw = work / "clips.json"
    edl_path = work / "edl.json"
    wide_out = work / "edit_wide.mp4" if want_vertical else out_mp4

    # 1) beat_map
    cmd = [py, str(REPO_ROOT / "beat_map.py"), str(audio), "-o", str(beatmap)]
    if args.html:
        cmd.append("--html")
    run_stage(cmd, "beat_map")

    # 2) clip_tag (file or folder)
    cmd = [
        py,
        str(REPO_ROOT / "clip_tag.py"),
        str(footage.resolve()),
        "-o",
        str(clips_raw),
        "--threshold",
        str(threshold),
    ]
    if args.html:
        cmd.append("--html")
    if args.thumbs:
        cmd.append("--thumbs")
    run_stage(cmd, "clip_tag")

    clips_abs = absolutize_clip_sources(clips_raw, videos)

    # 3) plan_edit — travel defaults
    lead = args.lead
    if not lead and calm_open > 0:
        lead = pick_calm_lead_ids(clips_abs, calm_open)

    cmd = [
        py,
        str(REPO_ROOT / "plan_edit.py"),
        str(beatmap),
        str(clips_abs),
        "-o",
        str(edl_path),
        "--beat-stride",
        str(beat_stride),
        "--segment",
        str(segment),
    ]
    if use_full:
        cmd.append("--full")
    if lead:
        cmd.extend(["--lead", lead])
    if args.exclude:
        cmd.extend(["--exclude", args.exclude])
    if args.pin:
        cmd.extend(["--pin", args.pin])
    if args.html:
        cmd.append("--html")
    run_stage(cmd, "plan_edit")

    if args.skip_render:
        print(f"\n✓ EDL ready (skip render): {edl_path}")
        return

    # 4) render_edit — -v fallback = first video; per-edit clip_source prefers abs paths
    cmd = [
        py,
        str(REPO_ROOT / "render_edit.py"),
        str(edl_path),
        "-a",
        str(audio.resolve()),
        "-v",
        str(videos[0]),
        "-o",
        str(wide_out),
    ]
    run_stage(cmd, "render_edit")

    final_path = wide_out
    if want_vertical:
        vert_out = out_mp4
        cmd = [
            py,
            str(REPO_ROOT / "vertical_style.py"),
            str(wide_out),
            "-o",
            str(vert_out),
            "--fit",
            str(v_fit),
            "--grade",
            str(v_grade),
            "--size",
            str(v_size),
        ]
        run_stage(cmd, "vertical_style")
        final_path = vert_out

    print("\n✓ Travel vlog done")
    print(f"  Output: {final_path}")
    print(f"  Work:   {work}")
    print(
        "  Note: Commercial / platform BGM is NOT free by default — "
        "clear Douyin/TikTok music rights yourself."
    )


if __name__ == "__main__":
    main()
