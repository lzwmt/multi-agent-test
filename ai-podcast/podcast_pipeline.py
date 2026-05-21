#!/usr/bin/env python3
"""
AI 播客音频管线 — 窄 MVP
输入：分段 JSON 脚本文件
输出：完整的 mp3 播客音频

用法：
  python3 podcast_pipeline.py script.json output.mp3 [--bgm-dir /path/to/bgm]

流程：
  1. 解析分段 JSON
  2. 逐段调用 MiMo TTS
  3. 生成段间静音
  4. 拼接：片头BGM + 各段 + 段间停顿 + 片尾BGM
  5. 音量标准化 (-16 LUFS)
"""

import json
import os
import subprocess
import sys
import tempfile
import shutil
from pathlib import Path

# === 配置 ===
TTS_SCRIPT = os.path.expanduser("~/.hermes/scripts/mimo-tts.sh")
SAMPLE_RATE = 24000
LUFS_TARGET = -16
DEFAULT_BGM_DIR = os.path.expanduser("~/.openclaw/workspace/ai-podcast/bgm")


def generate_placeholder_bgm(output_path: str, duration: float, freq: float = 440):
    """生成占位 BGM（简单正弦波），后续替换为真实 BGM"""
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i",
        f"sine=frequency={freq}:duration={duration}",
        "-af", f"volume=0.1,afade=t=in:st=0:d=0.5,afade=t=out:st={duration-0.5}:d=0.5",
        "-ar", str(SAMPLE_RATE),
        output_path
    ], capture_output=True, check=True)


def split_text(text: str, max_chars: int = 120) -> list:
    """将长文本按句子边界拆分成小块，每块不超过 max_chars 字符"""
    import re
    # 按中文句号、问号、感叹号、分号拆分
    sentences = re.split(r'(?<=[。！？；\n])', text)
    sentences = [s.strip() for s in sentences if s.strip()]

    chunks = []
    current = ""
    for sent in sentences:
        if len(current) + len(sent) <= max_chars:
            current += sent
        else:
            if current:
                chunks.append(current)
            current = sent
    if current:
        chunks.append(current)

    # 如果单句超过 max_chars，强制按逗号拆
    final = []
    for chunk in chunks:
        if len(chunk) <= max_chars:
            final.append(chunk)
        else:
            sub = re.split(r'(?<=[，,])', chunk)
            sub = [s.strip() for s in sub if s.strip()]
            buf = ""
            for s in sub:
                if len(buf) + len(s) <= max_chars:
                    buf += s
                else:
                    if buf:
                        final.append(buf)
                    buf = s
            if buf:
                final.append(buf)

    return final if final else [text]


def tts_segment(text: str, output_path: str):
    """调用 MiMo TTS 合成单段音频，自动拆分长文本"""
    chunks = split_text(text, max_chars=80)

    if len(chunks) == 1:
        # 单块，直接合成
        return _tts_single(chunks[0], output_path)

    # 多块，逐个合成后拼接
    import tempfile as _tmp
    tmpdir = _tmp.mkdtemp(prefix="tts_chunk_")
    chunk_files = []
    try:
        for i, chunk in enumerate(chunks):
            chunk_path = os.path.join(tmpdir, f"chunk_{i:03d}.wav")
            if not _tts_single(chunk, chunk_path):
                return False
            chunk_files.append(chunk_path)
            # 块间小停顿
            if i < len(chunks) - 1:
                pause_path = os.path.join(tmpdir, f"cpause_{i:03d}.wav")
                generate_silence(pause_path, 300)
                chunk_files.append(pause_path)
        concatenate_audio(chunk_files, output_path)
        return True
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def _tts_single(text: str, output_path: str, retries: int = 2) -> bool:
    """调用 MiMo TTS 合成单段音频（不含拆分逻辑），带重试"""
    import time
    for attempt in range(retries + 1):
        if attempt > 0:
            print(f"    ↻ 重试 {attempt}/{retries}...")
            time.sleep(3)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(text)
            input_path = f.name

        try:
            result = subprocess.run(
                ["bash", TTS_SCRIPT, input_path, output_path],
                capture_output=True, text=True, timeout=180
            )
            if result.returncode == 0:
                # P0-1: 验证输出文件存在且大小 > 0
                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    return True
                print(f"TTS 返回成功但文件为空: {output_path}", file=sys.stderr)
            print(f"TTS 失败: {result.stderr}", file=sys.stderr)
        except subprocess.TimeoutExpired:
            print("TTS 超时 (180s)", file=sys.stderr)
        finally:
            os.unlink(input_path)

            # 块间间隔，避免 API 限流
            time.sleep(3)

    return False


def generate_silence(output_path: str, duration_ms: int):
    """生成指定时长的静音"""
    duration_s = duration_ms / 1000.0
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i",
        f"anullsrc=r={SAMPLE_RATE}:cl=mono",
        "-t", str(duration_s),
        "-ar", str(SAMPLE_RATE),
        output_path
    ], capture_output=True, check=True)


def get_duration(filepath: str) -> float:
    """获取音频文件时长（秒）"""
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", filepath],
        capture_output=True, text=True
    )
    return float(result.stdout.strip())


def normalize_audio(input_path: str, output_path: str, target_lufs: float = LUFS_TARGET):
    """音量标准化到目标 LUFS"""
    # 先测量
    result = subprocess.run([
        "ffmpeg", "-y", "-i", input_path,
        "-af", f"loudnorm=I={target_lufs}:TP=-1.5:LRA=11:print_format=json",
        "-f", "null", "-"
    ], capture_output=True, text=True)

    # 从 stderr 提取 measured values
    stderr = result.stderr
    try:
        json_start = stderr.rfind("{")
        json_end = stderr.rfind("}") + 1
        if json_start >= 0:
            measured = json.loads(stderr[json_start:json_end])
            mi = measured.get("input_i", "-24")
            mtp = measured.get("input_tp", "-2")
            mlra = measured.get("input_lra", "11")
            mthresh = measured.get("input_thresh", "-34")
            mo = measured.get("target_offset", "0")

            subprocess.run([
                "ffmpeg", "-y", "-i", input_path,
                "-af", f"loudnorm=I={target_lufs}:TP=-1.5:LRA=11:measured_I={mi}:measured_TP={mtp}:measured_LRA={mlra}:measured_thresh={mthresh}:offset={mo}:linear=true",
                "-ar", str(SAMPLE_RATE),
                output_path
            ], capture_output=True, check=True)
            return
    except (json.JSONDecodeError, KeyError, ValueError):
        pass

    # fallback: 简单 volume 调整
    subprocess.run([
        "ffmpeg", "-y", "-i", input_path,
        "-af", f"volume=-16dB",
        "-ar", str(SAMPLE_RATE),
        output_path
    ], capture_output=True, check=True)


def concatenate_audio(parts: list, output_path: str):
    """拼接多个音频文件"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        for part in parts:
            f.write(f"file '{part}'\n")
        list_path = f.name

    try:
        subprocess.run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_path,
            "-ar", str(SAMPLE_RATE),
            "-ac", "1",
            output_path
        ], capture_output=True, check=True)
    finally:
        os.unlink(list_path)


def main():
    if len(sys.argv) < 3:
        print("用法: python3 podcast_pipeline.py <script.json> <output.mp3> [--bgm-dir <dir>]")
        sys.exit(1)

    script_path = sys.argv[1]
    output_path = sys.argv[2]
    bgm_dir = DEFAULT_BGM_DIR

    if "--bgm-dir" in sys.argv:
        idx = sys.argv.index("--bgm-dir")
        bgm_dir = sys.argv[idx + 1]

    # 读取脚本
    with open(script_path) as f:
        segments = json.load(f)

    print(f"📖 脚本加载: {len(segments)} 个段落")

    # 创建临时目录
    tmpdir = tempfile.mkdtemp(prefix="podcast_")
    parts = []

    try:
        # === 片头 BGM ===
        intro_bgm = os.path.join(bgm_dir, "intro.mp3")
        if os.path.exists(intro_bgm):
            print("🎵 使用已有片头 BGM")
            parts.append(intro_bgm)
        else:
            print("🎵 生成占位片头 BGM (3s)")
            placeholder = os.path.join(tmpdir, "intro_bgm.wav")
            generate_placeholder_bgm(placeholder, 3.0, freq=523)
            parts.append(placeholder)

        # === 逐段 TTS ===
        for i, seg in enumerate(segments):
            seg_type = seg.get("type", "topic")
            text = seg["text"]
            pause_ms = seg.get("pause_after_ms", 0)

            print(f"🎙️  [{i+1}/{len(segments)}] TTS: {seg_type} ({len(text)}字)")
            tts_out = os.path.join(tmpdir, f"seg_{i:03d}.wav")

            if not tts_segment(text, tts_out):
                # P0-2: TTS 失败时用静音替代，不跳过整段
                print(f"⚠️ 段落 {i+1} TTS 失败，使用静音替代", file=sys.stderr)
                # 估算文本时长：中文约 4 字/秒
                estimated_duration_ms = max(3000, len(text) * 250)
                generate_silence(tts_out, estimated_duration_ms)

            parts.append(tts_out)

            # 段间停顿
            if pause_ms > 0 and i < len(segments) - 1:
                silence = os.path.join(tmpdir, f"pause_{i:03d}.wav")
                generate_silence(silence, pause_ms)
                parts.append(silence)

            # 段间冷却，避免 API 限流
            if i < len(segments) - 1:
                import time
                time.sleep(2)

        # === 片尾 BGM ===
        outro_bgm = os.path.join(bgm_dir, "outro.mp3")
        if os.path.exists(outro_bgm):
            print("🎵 使用已有片尾 BGM")
            parts.append(outro_bgm)
        else:
            print("🎵 生成占位片尾 BGM (5s)")
            placeholder = os.path.join(tmpdir, "outro_bgm.wav")
            generate_placeholder_bgm(placeholder, 5.0, freq=392)
            parts.append(placeholder)

        # === 拼接 ===
        raw_concat = os.path.join(tmpdir, "raw_concat.wav")
        print("🔗 拼接音频...")
        concatenate_audio(parts, raw_concat)

        # === 标准化 ===
        print("📊 音量标准化...")
        normalize_audio(raw_concat, output_path)

        # === 完成 ===
        duration = get_duration(output_path)
        size_mb = os.path.getsize(output_path) / 1024 / 1024
        print(f"\n✅ 完成: {output_path}")
        print(f"   时长: {duration:.1f}s ({duration/60:.1f}min)")
        print(f"   大小: {size_mb:.1f}MB")

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    main()
