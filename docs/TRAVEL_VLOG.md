# Travel Vlog (卡点旅游) guide

Beat-synced travel edits: music + trip footage → cut on (thinned) beats → optional Douyin 9:16.

Upstream pipeline is unchanged: `beat_map` → `clip_tag` → `plan_edit` → `render_edit`.  
This fork adds `travel_vlog.py`, preset `presets/travel_vlog.json`, and docs.

Fork of [ZiadAbdelkarim/beat-synced-edit](https://github.com/ZiadAbdelkarim/beat-synced-edit) (MIT).

## Recommended shot order

Film (or sort) with a loose story arc so even automatic energy matching feels intentional:

1. **Establishing** — wide city / mountain / hotel morning (low motion)
2. **Transit** — train, airport, walking streets (medium motion)
3. **Landmarks** — hero buildings, viewpoints (mix)
4. **Food** — close-ups, steam, plating (medium)
5. **People** — friends, locals, reactions (higher energy)
6. **Sunset / outro** — skyline dusk, packing, credits-friendly calm

`travel_vlog.py` forces a **calm open** (lowest-motion clips as `--lead`) so the first cuts feel like establishing shots, then the matcher raises energy toward peaks.

## Beat-stride tips

| `--beat-stride` | Feel | When |
|---|---|---|
| `1` | Cut every beat | High-BPM club / hyper montages |
| **`2` (default)** | Every other beat — **breathes** | Most travel vlogs |
| `3`–`4` | Long holds | Scenic, drone, contemplative |

Rule of thumb: slower BGM or landscape → higher stride. Faster city pop → `2` (or `1` for drops only via shorter segments).

## Vertical / Douyin

```bash
python travel_vlog.py bgm.mp3 trip_folder/ --vertical -o out/douyin.mp4
```

Uses `vertical_style.py` (default travel grade: `warm`, size `1080x1920`).  
Override: `--vertical-grade teal-orange --vertical-fit cover`.

## BGM copyright warning (Douyin / TikTok / Reels)

**Do not assume commercial or chart music is free to use.**

- Platform “library” tracks ≠ your local MP3 is cleared.
- Using uncleared BGM can mute, block, or demonetize the post.
- Prefer: platform commercial music library, licensed stock, or music you own/composed.
- This tool **never** grants music rights — it only syncs picture to whatever file you pass.

## vs 口播粗剪 (`jianying-windows-workflow`)

| | **beat-synced-edit / travel_vlog** | **jianying-windows-workflow** |
|---|---|---|
| Goal | Music-driven **卡点** travel montage | Talking-head **口播** rough cut |
| Input | BGM + B-roll / trip clips | ASR JSON + talking-head MP4 |
| Logic | Beats + motion/energy tags | Pause / filler heuristics → keep segments |
| Output | Final(ish) MP4 (+ optional 9:16) | `rough.mp4` + optional Jianying draft scaffold |
| Editor | Optional; often post-ready | Designed to open in 剪映 for fine cut |

Use **travel_vlog** for scenic trip cards; use **jw_win** when the spine is spoken narration.

## Windows notes

1. Install [Python 3.10+](https://www.python.org/downloads/) (check “Add to PATH”).
2. Install ffmpeg: `winget install ffmpeg` or official builds; confirm `ffmpeg -version` in **cmd** or PowerShell.
3. `pip install -r requirements.txt`
4. Run from the repo folder: `python travel_vlog.py ...`

Paths with spaces: quote them (`"D:\My Trip\day1"`).
