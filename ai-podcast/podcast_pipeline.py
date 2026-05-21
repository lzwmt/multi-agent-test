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
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, APIC, TDRC, TRCK, COMM
from datetime import datetime, timezone, timedelta
import xml.etree.ElementTree as ET

# === 配置 ===
TTS_SCRIPT = os.path.expanduser("~/.hermes/scripts/mimo-tts.sh")
SAMPLE_RATE = 24000
LUFS_TARGET = -16
DEFAULT_BGM_DIR = os.path.expanduser("~/.openclaw/workspace/ai-podcast/bgm")
DEFAULT_COVER = os.path.expanduser("~/.openclaw/workspace/ai-podcast/rss/cover.png")
PODCAST_TITLE = "程序员赚钱指南"
PODCAST_AUTHOR = "lzwmt"
PODCAST_ALBUM = "程序员赚钱指南"
RSS_FEED_PATH = os.path.expanduser("~/.openclaw/workspace/ai-podcast/rss/feed.xml")
RSS_BASE_URL = "https://lzwmt.github.io/ai-podcast-rss"


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


def write_id3_tags(mp3_path: str, title: str, artist: str, album: str,
                   cover_path: str = None, episode_num: int = 1,
                   comment: str = ""):
    """写入 ID3 tags 和封面图到 MP3 文件"""
    try:
        audio = MP3(mp3_path)
        if audio.tags is None:
            audio.add_tags()
        
        tags = audio.tags
        tags.add(TIT2(encoding=3, text=title))
        tags.add(TPE1(encoding=3, text=artist))
        tags.add(TALB(encoding=3, text=album))
        tags.add(TRCK(encoding=3, text=str(episode_num)))
        tags.add(TDRC(encoding=3, text="2026"))
        
        if comment:
            tags.add(COMM(encoding=3, lang="zho", desc="", text=comment))
        
        # P1-9: 嵌入封面图
        if cover_path and os.path.exists(cover_path):
            with open(cover_path, "rb") as f:
                cover_data = f.read()
            tags.add(APIC(
                encoding=3,
                mime="image/png",
                type=3,  # Cover (front)
                desc="Cover",
                data=cover_data
            ))
        
        audio.save()
        print(f"  ✅ ID3 tags 已写入: {title}")
    except Exception as e:
        print(f"  ⚠️ ID3 tags 写入失败: {e}", file=sys.stderr)


def update_rss_feed(episode_num: int, title: str, description: str,
                    audio_filename: str, audio_size: int, duration_seconds: float):
    """更新 RSS feed.xml，添加新一期节目"""
    try:
        if not os.path.exists(RSS_FEED_PATH):
            print(f"  ⚠️ RSS feed 不存在: {RSS_FEED_PATH}", file=sys.stderr)
            return
        
        tree = ET.parse(RSS_FEED_PATH)
        root = tree.getroot()
        channel = root.find("channel")
        
        if channel is None:
            print("  ⚠️ RSS feed 格式错误: 缺少 channel", file=sys.stderr)
            return
        
        # 更新 lastBuildDate
        now = datetime.now(timezone(timedelta(hours=8)))
        now_str = now.strftime("%a, %d %b %Y %H:%M:%S %z")
        last_build = channel.find("lastBuildDate")
        if last_build is not None:
            last_build.text = now_str
        
        # 检查是否已存在该集数
        for item in channel.findall("item"):
            guid = item.find("guid")
            if guid is not None and guid.text == f"ep{episode_num:02d}-{now.strftime('%Y%m%d')}":
                print(f"  ℹ️ EP{episode_num:02d} 已存在于 RSS feed", file=sys.stderr)
                return
        
        # 创建新 item
        item = ET.SubElement(channel, "item")
        
        title_el = ET.SubElement(item, "title")
        title_el.text = title
        
        itunes_title = ET.SubElement(item, "{http://www.itunes.com/dtds/podcast-1.0.dtd}title")
        itunes_title.text = title
        
        itunes_episode = ET.SubElement(item, "{http://www.itunes.com/dtds/podcast-1.0.dtd}episode")
        itunes_episode.text = str(episode_num)
        
        itunes_duration = ET.SubElement(item, "{http://www.itunes.com/dtds/podcast-1.0.dtd}duration")
        itunes_duration.text = str(int(duration_seconds))
        
        itunes_summary = ET.SubElement(item, "{http://www.itunes.com/dtds/podcast-1.0.dtd}summary")
        itunes_summary.text = description
        
        desc_el = ET.SubElement(item, "description")
        desc_el.text = description
        
        pub_date = ET.SubElement(item, "pubDate")
        pub_date.text = now_str
        
        enclosure = ET.SubElement(item, "enclosure")
        enclosure.set("url", f"{RSS_BASE_URL}/episodes/{audio_filename}")
        enclosure.set("length", str(audio_size))
        enclosure.set("type", "audio/mpeg")
        
        link = ET.SubElement(item, "link")
        link.text = RSS_BASE_URL
        
        guid = ET.SubElement(item, "guid")
        guid.set("isPermaLink", "false")
        guid.text = f"ep{episode_num:02d}-{now.strftime('%Y%m%d')}"
        
        # 保存
        tree.write(RSS_FEED_PATH, encoding="unicode", xml_declaration=True)
        print(f"  ✅ RSS feed 已更新: EP{episode_num:02d}")
        
    except Exception as e:
        print(f"  ⚠️ RSS feed 更新失败: {e}", file=sys.stderr)


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
            # 转换为WAV格式以确保拼接兼容性
            intro_wav = os.path.join(tmpdir, "intro_bgm.wav")
            subprocess.run([
                "ffmpeg", "-y", "-i", intro_bgm,
                "-ar", str(SAMPLE_RATE), "-ac", "1",
                intro_wav
            ], capture_output=True, check=True)
            parts.append(intro_wav)
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
            # 转换为WAV格式以确保拼接兼容性
            outro_wav = os.path.join(tmpdir, "outro_bgm.wav")
            subprocess.run([
                "ffmpeg", "-y", "-i", outro_bgm,
                "-ar", str(SAMPLE_RATE), "-ac", "1",
                outro_wav
            ], capture_output=True, check=True)
            parts.append(outro_wav)
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

        # === P1-8/P1-9: 写入 ID3 tags + 封面图 ===
        episode_num = len([s for s in segments if s.get("type") == "topic"])  # 估算集数
        episode_title = f"EP{episode_num:02d}: {segments[0]['text'][:30]}..." if segments else "EP01"
        cover_path = os.path.join(os.path.dirname(output_path), "cover.png")
        if not os.path.exists(cover_path):
            cover_path = DEFAULT_COVER
        print("🏷️ 写入 ID3 tags + 封面图...")
        write_id3_tags(
            output_path,
            title=episode_title,
            artist=PODCAST_AUTHOR,
            album=PODCAST_ALBUM,
            cover_path=cover_path if os.path.exists(cover_path) else None,
            episode_num=episode_num,
            comment=f"AI × 投资 | 每天 5-8 分钟 | {PODCAST_TITLE}"
        )

        # === P1-10: 自动更新 RSS feed ===
        print("📡 更新 RSS feed...")
        update_rss_feed(
            episode_num=episode_num,
            title=episode_title,
            description=segments[0]['text'][:200] if segments else "",
            audio_filename=os.path.basename(output_path),
            audio_size=os.path.getsize(output_path),
            duration_seconds=get_duration(output_path)
        )

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
