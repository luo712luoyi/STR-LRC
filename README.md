# SRT → LRC 字幕/歌词转换器

将 SRT 字幕文件转换为 LRC 歌词文件，方便导入音乐播放器实现同步歌词显示。

## 功能特点

-  **精准转换** — 完整解析 SRT 时间轴，生成标准 LRC 时间标签 `[mm:ss.xx]`
-  **批量处理** — 支持单个文件、整个目录、或通配符批量转换
-  **智能合并** — 间隔小于 0.3 秒的相邻字幕自动合并（同一句歌词换行显示）
-  **编码自适应** — 自动检测 UTF-8 / GBK / Big5 等多种编码，也可手动指定
-  **纯 Python** — 无第三方依赖，标准库即可运行

## 快速开始

### 环境要求

- Python 3.7+

### 基本用法

```bash
# 转换单个文件
python convert.py  input.srt

# 批量转换当前目录所有 .srt 文件
python convert.py  *.srt

# 转换整个目录
python convert.py  srt_folder/

# 指定输出文件名（仅单文件时可用）
python convert.py  input.srt  -o output.lrc
```

### Windows 用户

可直接使用 `convert.bat`，效果等同 `python convert.py`：

```bat
convert.bat input.srt
```

### 高级选项

```bash
# 指定源文件编码（跳过自动检测）
python convert.py  input.srt  --enc gbk

# 指定输出编码
python convert.py  input.srt  --output-enc utf-8

# 输出到指定目录
python convert.py  srt_folder/  --outdir lrc_output/

# 调整合并间隔（秒），设为 -1 禁用合并
python convert.py  input.srt  --merge-gap 0.5

# 静默模式
python convert.py  *.srt  -q
```

### 完整选项

| 参数 | 说明 |
|------|------|
| `input` | SRT 文件路径或包含 SRT 文件的目录（可多个） |
| `-o, --output` | 输出文件名（仅单文件时可用） |
| `--outdir` | 输出目录，默认与输入文件同目录 |
| `--enc` | 源编码，如 `utf-8` / `gbk`（默认自动检测） |
| `--output-enc` | 输出编码，默认 `utf-8` |
| `--merge-gap` | 合并间隔秒数，默认 `0.3`，设为 `-1` 禁用 |
| `-q, --quiet` | 静默模式，仅显示错误 |

## 转换示例

**输入** (`input.srt`):
```
1
00:00:01,500 --> 00:00:04,200
Hello, world!

2
00:00:04,300 --> 00:00:07,800
This is a subtitle file.

3
00:00:08,000 --> 00:00:12,500
Line one
Line two of the same subtitle
```

**输出** (`input.lrc`):
```lrc
[00:01.50]Hello, world! \ This is a subtitle file.
[00:08.00]Line one Line two of the same subtitle
```

> 第一、二条字幕间隔 0.1 秒（小于默认合并阈值 0.3 秒），自动合并为一行。

## 文件说明

| 文件 | 说明 |
|------|------|
| `convert.py` | 主程序（Python 脚本） |
| `convert.bat` | Windows 批处理封装（自动设置 UTF-8 编码） |

## 编码支持

自动检测以下编码（按优先级）：

1. `utf-8` / `utf-8-sig`（带 BOM）
2. `gbk` / `gb2312` / `gb18030`（中文简繁）
3. `big5`（繁体中文）
4. `latin-1`（回退编码）

也可通过 `--enc` 手动指定。

## 许可证

MIT
