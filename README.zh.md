# Beat-Synced Edit — 卡点旅游 Vlog（中文说明）

本仓库是 [ZiadAbdelkarim/beat-synced-edit](https://github.com/ZiadAbdelkarim/beat-synced-edit) 的 fork（**MIT**），保留上游全部 CLI，并增加 **旅游卡点一键流水线**。

英文总览见 [README.md](README.md)；旅游专题见 [docs/TRAVEL_VLOG.md](docs/TRAVEL_VLOG.md)。

## 怎么装（Windows + ffmpeg）

1. 安装 **Python 3.10+**（安装勾选加入 PATH）。
2. 安装 **ffmpeg** 并确认在 PATH 中：
   - 推荐：`winget install ffmpeg`
   - 或从 [ffmpeg.org](https://ffmpeg.org/download.html) 下载，把 `bin` 加到系统环境变量
   - 验证：打开 cmd / PowerShell，执行 `ffmpeg -version`
3. 克隆本仓库并安装依赖：

```bat
git clone https://github.com/kotori759248375/beat-synced-edit.git
cd beat-synced-edit
python -m pip install -r requirements.txt
python travel_vlog.py --doctor
```

macOS：`brew install ffmpeg`；Linux：用发行版包管理器安装 `ffmpeg`。

## 一键：音乐 + 行程素材 → 成片

```bat
python travel_vlog.py bgm.mp3 D:\trip\clips\ -o out\travel_vlog.mp4
```

抖音竖屏（9:16）：

```bat
python travel_vlog.py bgm.mp3 D:\trip\clips\ --vertical -o out\douyin.mp4
```

等价：`python -m travel_vlog ...`（在仓库根目录执行）。

流水线：`beat_map` → `clip_tag` → `plan_edit` → `render_edit`（可选 `vertical_style`）。

## 旅游卡点推荐参数

| 参数 | 默认（`presets/travel_vlog.json`） | 说明 |
|---|---|---|
| `--beat-stride` | **2** | 每隔一拍切一次，镜头更「呼吸」，避免每拍硬切 |
| 冷静开场 | 开场 2 个低运动镜头 | 优先大景 / 建立镜头，再抬能量 |
| `--vertical` | 关 | 转 1080×1920，旅游预设调色 `warm` |
| `--full` | 关 | 默认只剪歌曲能量最高片段；加 `--full` 剪整首 |

更多：`python travel_vlog.py --help`

仍可用上游四段式 CLI（行为不变），见英文 README。

## 与口播粗剪 jianying-windows-workflow 的区别

| | 本仓库 `travel_vlog` | `jianying-windows-workflow`（口播粗剪） |
|---|---|---|
| 用途 | **旅游 / B-roll 卡点**，跟鼓点跳舞 | **口播**删停顿、口头禅，出粗剪 |
| 输入 | BGM + 行程视频文件夹 | ASR 词级 JSON + 口播原片 |
| 输出 | 可直接发的卡点 MP4（可竖屏） | rough.mp4 + 可选剪映草稿对接 |
| 是否替代剪映精修 | 常作成片或轻精修 | 面向剪映精修 |

口播项目请用 jianying-windows-workflow；**风景卡点用本工具**。

## BGM 版权（重要）

**不要默认商用 BGM / 本地 mp3 可在抖音免费使用。**  
平台曲库授权 ≠ 你自备音源已授权。侵权可能导致静音、无法推荐或下架。本工具**不提供**任何音乐版权。详见 [docs/TRAVEL_VLOG.md](docs/TRAVEL_VLOG.md)。

## 许可

MIT。上游版权归属 Ziad Abdelkarim；本 fork 仅增加旅游向文档与入口，未移除上游脚本。
