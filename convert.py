#!/usr/bin/env python3
"""
SRT to LRC Subtitle Converter
==============================
将 SRT 字幕文件转换为 LRC 歌词文件。

用法:
  python convert.py input.srt                    # 转换单个文件
  python convert.py folder/                      # 转换文件夹下所有 .srt 文件
  python convert.py *.srt                        # 批量转换多个文件
  python convert.py input.srt -o output.lrc      # 指定输出文件名
  python convert.py input.srt --enc gbk          # 指定源文件编码
"""

import os
import re
import sys
import argparse


# ── SRT 解析 ──────────────────────────────────────────────────────────────

SRT_BLOCK_RE = re.compile(
    r"(\d+)\s*\n"               # 序号
    r"(\d{2}:\d{2}:\d{2}[,\.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,\.]\d{3})"  # 时间轴
    r"\s*\n(.*?)(?=\n\s*\n|\Z)",
    re.DOTALL,
)


def parse_srt_timestamp(ts: str) -> float:
    """将 SRT 时间戳 (hh:mm:ss,mmm / hh:mm:ss.mmm) 转为秒数。"""
    ts = ts.replace(",", ".")
    parts = ts.split(":")
    h, m = int(parts[0]), int(parts[1])
    s_parts = parts[2].split(".")
    s, ms = int(s_parts[0]), int(s_parts[1].ljust(3, "0")[:3])
    return h * 3600 + m * 60 + s + ms / 1000.0


def parse_srt(text: str):
    """
    解析 SRT 文本，产出字典列表：
      { "index": int, "start": float, "end": float, "text": str }
    """
    blocks = []
    for match in SRT_BLOCK_RE.finditer(text.strip() + "\n\n"):
        index = int(match.group(1))
        start = parse_srt_timestamp(match.group(2))
        end = parse_srt_timestamp(match.group(3))
        raw_text = match.group(4).strip()
        # 清理行内 HTML / 样式标签
        clean = re.sub(r"<[^>]+>", "", raw_text)
        # 合并多行文本（用空格连接）
        clean = " ".join(line.strip() for line in clean.splitlines() if line.strip())
        blocks.append({"index": index, "start": start, "end": end, "text": clean})
    return blocks


# ── LRC 生成 ──────────────────────────────────────────────────────────────

def seconds_to_lrc_time(sec: float) -> str:
    """将秒数转为 LRC 时间标签 [mm:ss.xx]。"""
    m = int(sec // 60)
    s = int(sec % 60)
    cs = int(round((sec - int(sec)) * 100))
    # 防止 60.00 溢出
    if cs >= 100:
        s += 1
        cs = 0
    if s >= 60:
        m += 1
        s = 0
    return f"[{m:02d}:{s:02d}.{cs:02d}]"


def blocks_to_lrc(blocks, merge_gap: float = 0.3) -> str:
    """
    将解析后的字幕块转为 LRC 文本。
    - 默认合并间隔小于 merge_gap 秒且文本相邻的内容（同一句歌词换行显示）。
    - 若不想合并，传入 merge_gap = -1。
    """
    if not blocks:
        return ""

    lines = []
    # 可选：在开头添加元信息
    # lines.append("[ti:标题]")
    # lines.append("[ar:歌手]")
    # lines.append("[by:转换自 SRT]")

    i = 0
    while i < len(blocks):
        block = blocks[i]
        # 检查是否需要与后续块合并
        if (
            merge_gap >= 0
            and i + 1 < len(blocks)
            and (blocks[i + 1]["start"] - block["end"]) < merge_gap
        ):
            # 合并连续的几条字幕
            combined_text = block["text"]
            j = i + 1
            while (
                j < len(blocks)
                and (blocks[j]["start"] - blocks[j - 1]["end"]) < merge_gap
            ):
                combined_text += " \\ " + blocks[j]["text"]
                j += 1
            lines.append(f"{seconds_to_lrc_time(block['start'])}{combined_text}")
            i = j
        else:
            lines.append(f"{seconds_to_lrc_time(block['start'])}{block['text']}")
            i += 1

    return "\n".join(lines) + "\n"


# ── 文件 I/O ──────────────────────────────────────────────────────────────

ENCODINGS = ["utf-8", "utf-8-sig", "gbk", "gb2312", "gb18030", "big5", "latin-1"]


def detect_and_read(path: str, enc_hint: str | None = None) -> str | None:
    """
    尝试用多种编码读取文件。
    如果 enc_hint 指定，优先使用该编码。
    返回文件内容，失败返回 None。
    """
    candidates = [enc_hint] if enc_hint else ENCODINGS
    for enc in candidates:
        if enc is None:
            continue
        try:
            with open(path, "r", encoding=enc) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
        except Exception as e:
            print(f"  [!] 读取文件出错: {e}", file=sys.stderr)
            return None
    return None


def convert_file(
    srt_path: str,
    lrc_path: str | None = None,
    *,
    enc: str | None = None,
    merge_gap: float = 0.3,
    encoding_out: str = "utf-8",
) -> bool:
    """将单个 SRT 文件转换为 LRC 文件。成功返回 True。"""
    srt_name = os.path.basename(srt_path)
    if not lrc_path:
        lrc_path = os.path.splitext(srt_path)[0] + ".lrc"

    content = detect_and_read(srt_path, enc)
    if content is None:
        print(f"  [ERR] 无法读取（编码无效）: {srt_name}")
        return False

    blocks = parse_srt(content)
    if not blocks:
        print(f"  [ERR] 未找到有效字幕: {srt_name}")
        return False

    lrc_text = blocks_to_lrc(blocks, merge_gap)

    try:
        with open(lrc_path, "w", encoding=encoding_out, newline="\n") as f:
            f.write(lrc_text)
    except Exception as e:
        print(f"  [ERR] 写入失败: {lrc_path} — {e}", file=sys.stderr)
        return False

    print(f"  [OK] {srt_name}  →  {os.path.basename(lrc_path)}  ({len(blocks)} 条字幕)")
    return True


# ── 主入口 ────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="将 SRT 字幕文件转换为 LRC 歌词文件。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例:\n"
            "  %(prog)s input.srt                        转换单个文件\n"
            "  %(prog)s input.srt -o output.lrc          指定输出文件名\n"
            "  %(prog)s srt/ --outdir lrc/               处理整个目录\n"
            "  %(prog)s *.srt                            批量转换\n"
            "  %(prog)s input.srt --enc gbk              指定源编码（默认自动检测）\n"
        ),
    )
    parser.add_argument("input", nargs="+", help="SRT 文件或包含 SRT 文件的目录")
    parser.add_argument("-o", "--output", help="输出文件名（仅单文件时可用）")
    parser.add_argument("--outdir", help="输出目录（默认与输入文件同目录）")
    parser.add_argument("--enc", help="源文件编码，如 utf-8 / gbk（默认自动检测）")
    parser.add_argument(
        "--output-enc", default="utf-8",
        help="输出文件编码（默认 utf-8）",
    )
    parser.add_argument(
        "--merge-gap", type=float, default=0.3,
        help="合并字幕的最大间隔秒数（默认 0.3，设为 -1 禁用合并）",
    )
    parser.add_argument(
        "-q", "--quiet", action="store_true",
        help="静默模式，只显示错误",
    )

    args = parser.parse_args()

    # 收集所有待处理的 .srt 路径
    srt_files: list[str] = []
    for inp in args.input:
        if os.path.isfile(inp):
            if inp.lower().endswith(".srt"):
                srt_files.append(inp)
            elif not args.quiet:
                print(f"  跳过非 .srt 文件: {inp}")
        elif os.path.isdir(inp):
            for entry in sorted(os.listdir(inp)):
                full = os.path.join(inp, entry)
                if entry.lower().endswith(".srt") and os.path.isfile(full):
                    srt_files.append(full)
        else:
            print(f"  [WARN] 路径不存在: {inp}", file=sys.stderr)

    if not srt_files:
        print("没有找到任何 .srt 文件。")
        sys.exit(1)

    # 校验：指定了 -o 但文件数 > 1
    if args.output and len(srt_files) > 1:
        print("错误：-o / --output 只能用于单个文件转换。", file=sys.stderr)
        sys.exit(2)

    success = 0
    for srt_path in srt_files:
        if args.output:
            lrc_path = args.output
        elif args.outdir:
            base = os.path.splitext(os.path.basename(srt_path))[0]
            lrc_path = os.path.join(args.outdir, base + ".lrc")
        else:
            lrc_path = os.path.splitext(srt_path)[0] + ".lrc"

        ok = convert_file(
            srt_path,
            lrc_path,
            enc=args.enc,
            merge_gap=args.merge_gap,
            encoding_out=args.output_enc,
        )
        if ok:
            success += 1

    total = len(srt_files)
    if not args.quiet:
        print(f"\n处理完成: {success}/{total} 个文件成功转换。")

    sys.exit(0 if success == total else 1)


if __name__ == "__main__":
    main()
