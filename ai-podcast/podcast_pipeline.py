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

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
import shutil
import uuid
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import yaml
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
DEFAULT_TTS_CACHE_DIR = os.path.expanduser("~/.openclaw/workspace/ai-podcast/output/tts_cache")
DEFAULT_TTS_WORKERS = int(os.environ.get("PODCAST_TTS_WORKERS", "2"))
DEFAULT_TTS_TIMEOUT = int(os.environ.get("PODCAST_TTS_TIMEOUT", "120"))
PODCAST_TITLE = "代码与财富"
PODCAST_AUTHOR = "lzwmt"
PODCAST_ALBUM = "代码与财富"
RSS_FEED_PATH = os.path.expanduser("~/.openclaw/workspace/ai-podcast/rss/feed.xml")
RSS_BASE_URL = "https://lzwmt.github.io/ai-podcast-rss"


def load_runtime_env() -> dict:
    """Load TTS credentials from Hermes env/config for direct pipeline runs."""
    env = os.environ.copy()
    env_path = Path("/root/.hermes/.env")
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            if not line or line.lstrip().startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key in {"XIAOMI_API_KEY", "XIAOMI_BASE_URL", "AINAIBA_API_KEY", "AINAIBA_API_URL"}:
                env.setdefault(key, value)

    config_path = Path("/root/.hermes/config.yaml")
    if (not env.get("AINAIBA_API_KEY") or not env.get("AINAIBA_API_URL")) and config_path.exists():
        cfg = yaml.safe_load(config_path.read_text(encoding="utf-8", errors="ignore")) or {}
        for provider in cfg.get("custom_providers", []):
            base_url = provider.get("base_url", "")
            name = provider.get("name", "")
            if "ainaiba" in base_url.lower() or "api-xai" in base_url.lower() or "ainaiba" in name.lower():
                if provider.get("api_key"):
                    env.setdefault("AINAIBA_API_KEY", provider["api_key"])
                if base_url:
                    env.setdefault("AINAIBA_API_URL", base_url)
                break
    return env


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


def tts_cache_path(text: str, cache_dir: str) -> str:
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:24]
    return os.path.join(cache_dir, f"mimo_{digest}.wav")


def tts_chunk_cached(text: str, cache_dir: str, no_cache: bool = False,
                     timeout: int = DEFAULT_TTS_TIMEOUT) -> str | None:
    """Return a WAV path for one text chunk, using content-addressed cache."""
    os.makedirs(cache_dir, exist_ok=True)
    cached = tts_cache_path(text, cache_dir)
    if not no_cache and os.path.exists(cached) and os.path.getsize(cached) > 0:
        return cached
    tmp_out = cached + f".{os.getpid()}.{uuid.uuid4().hex}.tmp.wav"
    if _tts_single(text, tmp_out, timeout=timeout):
        if not no_cache and os.path.exists(cached) and os.path.getsize(cached) > 0:
            os.unlink(tmp_out)
            return cached
        os.replace(tmp_out, cached)
        return cached
    if os.path.exists(tmp_out):
        os.unlink(tmp_out)
    return None


def tts_segment(text: str, output_path: str, cache_dir: str = DEFAULT_TTS_CACHE_DIR,
                workers: int = DEFAULT_TTS_WORKERS, no_cache: bool = False,
                timeout: int = DEFAULT_TTS_TIMEOUT):
    """调用 MiMo TTS 合成单段音频，自动拆分长文本，失败后降级串行。"""
    chunks = split_text(text, max_chars=80)
    first_workers = max(1, min(workers, len(chunks)))
    tmpdir = tempfile.mkdtemp(prefix="tts_chunk_")

    def synthesize(active_workers: int) -> dict:
        results = {}
        if active_workers == 1:
            for i, chunk in enumerate(chunks):
                results[i] = tts_chunk_cached(chunk, cache_dir, no_cache=no_cache, timeout=timeout)
        else:
            with ThreadPoolExecutor(max_workers=active_workers) as pool:
                futures = {
                    pool.submit(tts_chunk_cached, chunk, cache_dir, no_cache, timeout): i
                    for i, chunk in enumerate(chunks)
                }
                for future in as_completed(futures):
                    idx = futures[future]
                    results[idx] = future.result()
                    if not results[idx]:
                        print(f"  ⚠️ chunk {idx} 失败", file=sys.stderr)
        return results

    try:
        results = synthesize(first_workers)
        failed = [i for i in range(len(chunks)) if not results.get(i)]
        if failed and first_workers > 1:
            print(f"  ⚠️ 并发 TTS 失败 chunks={failed}，降级串行重试", file=sys.stderr)
            retry_results = synthesize(1)
            for idx in failed:
                results[idx] = retry_results.get(idx)
            failed = [i for i in range(len(chunks)) if not results.get(i)]
        if failed:
            print(f"  ❌ TTS 段落失败 chunks={failed}，停止生成，避免静音冒充成品", file=sys.stderr)
            return False

        ordered_files = []
        for i in range(len(chunks)):
            ordered_files.append(results[i])
            if i < len(chunks) - 1:
                pause_path = os.path.join(tmpdir, f"cpause_{i:03d}.wav")
                generate_silence(pause_path, 300)
                ordered_files.append(pause_path)

        concatenate_audio(ordered_files, output_path)
        return True
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def _tts_single(text: str, output_path: str, retries: int = 1,
                timeout: int = DEFAULT_TTS_TIMEOUT) -> bool:
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
                capture_output=True, text=True, timeout=timeout, env=load_runtime_env()
            )
            if result.returncode == 0:
                # P0-1: 验证输出文件存在且大小 > 0
                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    return True
                print(f"TTS 返回成功但文件为空: {output_path}", file=sys.stderr)
            print(f"TTS 失败: {result.stderr}", file=sys.stderr)
        except subprocess.TimeoutExpired:
            print(f"TTS 超时 ({timeout}s)", file=sys.stderr)
        finally:
            os.unlink(input_path)

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
    parser = argparse.ArgumentParser(description="AI 播客音频管线")
    parser.add_argument("script_path", help="分段 JSON 脚本")
    parser.add_argument("output_path", help="输出 MP3")
    parser.add_argument("--bgm-dir", default=DEFAULT_BGM_DIR)
    parser.add_argument("--episode-num", type=int, default=1)
    parser.add_argument("--episode-title", default="")
    parser.add_argument("--description", default="")
    parser.add_argument("--no-rss", action="store_true", help="只生成音频，不更新 RSS")
    parser.add_argument("--tts-workers", type=int, default=DEFAULT_TTS_WORKERS, help="TTS chunk 并发数，默认读取 PODCAST_TTS_WORKERS 或 2")
    parser.add_argument("--tts-timeout", type=int, default=DEFAULT_TTS_TIMEOUT, help="单个 TTS chunk 超时时间，默认读取 PODCAST_TTS_TIMEOUT 或 120 秒")
    parser.add_argument("--tts-cache-dir", default=DEFAULT_TTS_CACHE_DIR, help="TTS WAV 缓存目录")
    parser.add_argument("--no-tts-cache", action="store_true", help="禁用 TTS 文本缓存")
    args = parser.parse_args()

    script_path = args.script_path
    output_path = args.output_path
    bgm_dir = args.bgm_dir

    # 读取脚本
    with open(script_path) as f:
        segments = json.load(f)

    print(f"📖 脚本加载: {len(segments)} 个段落")
    print(f"⚙️  TTS workers={args.tts_workers}, timeout={args.tts_timeout}s, cache={'off' if args.no_tts_cache else args.tts_cache_dir}")

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
        segment_audio = [None] * len(segments)
        print(f"🎙️  并行 TTS: {len(segments)} 段")

        def render_segment(index: int, seg: dict):
            seg_type = seg.get("type", "topic")
            text = seg["text"]
            tts_out = os.path.join(tmpdir, f"seg_{index:03d}.wav")
            started = time.time()
            print(f"🎙️  [{index+1}/{len(segments)}] TTS: {seg_type} ({len(text)}字)")
            ok = tts_segment(
                text,
                tts_out,
                cache_dir=args.tts_cache_dir,
                workers=args.tts_workers,
                no_cache=args.no_tts_cache,
                timeout=args.tts_timeout,
            )
            if not ok:
                raise RuntimeError(f"段落 {index+1} TTS 失败")
            return index, tts_out, time.time() - started

        with ThreadPoolExecutor(max_workers=max(1, min(args.tts_workers, len(segments)))) as pool:
            futures = {pool.submit(render_segment, i, seg): i for i, seg in enumerate(segments)}
            for future in as_completed(futures):
                index = futures[future]
                try:
                    index, tts_out, elapsed = future.result()
                except Exception as exc:
                    for pending in futures:
                        pending.cancel()
                    raise RuntimeError(f"段落 {index+1} TTS 失败: {exc}") from exc
                segment_audio[index] = tts_out
                print(f"  ✅ 段落 {index+1} 完成: {elapsed:.1f}s")

        for i, seg in enumerate(segments):
            parts.append(segment_audio[i])
            pause_ms = seg.get("pause_after_ms", 0)
            if pause_ms > 0 and i < len(segments) - 1:
                silence = os.path.join(tmpdir, f"pause_{i:03d}.wav")
                generate_silence(silence, pause_ms)
                parts.append(silence)

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
        episode_num = args.episode_num
        if args.episode_title:
            episode_title = args.episode_title
        elif segments:
            episode_title = f"EP{episode_num:02d}: {segments[0]['text'][:30]}..."
        else:
            episode_title = f"EP{episode_num:02d}"
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
        if not args.no_rss:
            print("📡 更新 RSS feed...")
            update_rss_feed(
                episode_num=episode_num,
                title=episode_title,
                description=args.description or (segments[0]['text'][:200] if segments else ""),
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
