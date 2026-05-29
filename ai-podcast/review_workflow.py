#!/usr/bin/env python3
"""
播客内容审核脚本
AI 生成内容后，推送给用户审核确认。

用法：
  python3 review_workflow.py --generate    # 生成今日内容（AI自动）
  python3 review_workflow.py --review      # 审核今日内容（你来）
  python3 review_workflow.py --approve     # 确认并发布
  python3 review_workflow.py --reject      # 拒绝，重新生成

流程：
  1. AI 自动：抓取新闻 → 分析 → 生成审核材料
  2. 你来审核：看选题 → 看分析 → 确认
  3. AI 自动：生成脚本 → TTS → 音频处理 → RSS → GitHub Pages
"""

import json
import os
import shutil
import subprocess
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from pathlib import Path

import yaml

# === 配置 ===
WORKSPACE = os.path.expanduser("~/.openclaw/workspace/ai-podcast")
OUTPUT_DIR = os.path.join(WORKSPACE, "output")
REVIEW_DIR = os.path.join(WORKSPACE, "review")
RSS_DIR = os.path.join(WORKSPACE, "rss")
RSS_FEED_PATH = os.path.join(RSS_DIR, "feed.xml")
RSS_EPISODES_DIR = os.path.join(RSS_DIR, "episodes")
RSS_BASE_URL = "https://lzwmt.github.io/ai-podcast-rss"
PODCAST_TITLE = "代码与财富"
PODCAST_AUTHOR = "lzwmt"

# 脚本路径
FETCH_SCRIPT = os.path.join(WORKSPACE, "fetch_podcast_news.py")
ANALYSIS_SCRIPT = os.path.join(WORKSPACE, "ai_investment_analysis.py")
PIPELINE_SCRIPT = os.path.join(WORKSPACE, "podcast_pipeline.py")
ITUNES_NS = "http://www.itunes.com/dtds/podcast-1.0.dtd"
ET.register_namespace("itunes", ITUNES_NS)


def load_runtime_env() -> dict:
    """Load credentials from Hermes env/config without sourcing shell files."""
    env = os.environ.copy()
    env_path = Path("/root/.hermes/.env")
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            if not line or line.lstrip().startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key in {"AINAIBA_API_KEY", "AINAIBA_API_URL", "XIAOMI_API_KEY", "XIAOMI_BASE_URL"}:
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


def find_today_review_file() -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    return os.path.join(REVIEW_DIR, f"{today}_pending.json")


def load_review_data(review_file: str) -> dict:
    with open(review_file, encoding="utf-8") as f:
        return json.load(f)


def save_review_data(review_file: str, data: dict) -> None:
    with open(review_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def mark_publish_step(review_file: str, data: dict, step: str, **values) -> dict:
    publish = data.setdefault("publish", {})
    if step != "last_error":
        publish.pop("last_error", None)
    publish[step] = {"ok": True, "at": datetime.now().isoformat(), **values}
    publish["last_step"] = step
    data["updated_at"] = datetime.now().isoformat()
    save_review_data(review_file, data)
    return data


def mark_publish_error(review_file: str, data: dict, step: str, error: str) -> None:
    data["status"] = "publish_failed"
    data.setdefault("publish", {})["last_error"] = {
        "step": step,
        "error": error,
        "at": datetime.now().isoformat(),
    }
    save_review_data(review_file, data)


def get_next_episode_number() -> int:
    if not os.path.exists(RSS_FEED_PATH):
        return 1
    tree = ET.parse(RSS_FEED_PATH)
    channel = tree.getroot().find("channel")
    if channel is None:
        return 1
    max_episode = 0
    for item in channel.findall("item"):
        ep = item.find(f"{{{ITUNES_NS}}}episode")
        if ep is not None and ep.text and ep.text.strip().isdigit():
            max_episode = max(max_episode, int(ep.text.strip()))
    return max_episode + 1


def make_episode_title(data: dict, episode_num: int) -> str:
    topic = data.get("selected_topic", {})
    title = topic.get("title") or "今日 AI 投资观察"
    title = title.replace("\n", " ").strip()
    return f"EP{episode_num:02d}: {title[:52]}"


def make_episode_summary(data: dict) -> str:
    topic = data.get("selected_topic", {})
    analysis = data.get("analysis", {})
    if isinstance(analysis, dict):
        summary = analysis.get("一句话总结") or analysis.get("核心发现") or analysis.get("raw_text")
        if summary:
            return str(summary).replace("\n", " ").strip()[:260]
    return (topic.get("summary") or topic.get("title") or "AI 投资主题深度分析").replace("\n", " ").strip()[:260]


def build_script_prompt(data: dict, episode_title: str) -> str:
    topic = data.get("selected_topic", {})
    analysis = data.get("analysis", {})
    news = data.get("news", [])[:5]
    news_lines = []
    for i, item in enumerate(news, 1):
        news_lines.append(
            f"{i}. [{item.get('source', '')}] {item.get('title', '')}\n"
            f"摘要: {item.get('summary', '')[:220]}"
        )
    analysis_text = json.dumps(analysis, ensure_ascii=False, indent=2) if analysis else ""
    return f"""你是播客「代码与财富」的脚本写手。请基于审核通过的选题生成一期完整口播脚本。

节目定位:
- 口号: 用代码理解世界，用AI管好钱包
- 人设: 一个用AI研究投资的程序员，真实、务实、技术派、学习者
- 总时长目标: 15-20分钟，总字数4800-5600字；低于4800字视为失败，必须扩写后再输出
- 内容配比: 60% 讲“我如何用 AI 分析这件事对投资/商业的影响”，25% 讲技术/产品本身，15% 讲风险和个人操作边界
- 生成前先在心里按段落预算字数，输出前自检总字数；不要输出自检过程，只输出 JSON
- 不能荐股，涉及投资必须说“这只是我的个人操作，不构成投资建议”
- 如果主选题偏技术新闻，也必须转译成“商业模式、成本结构、产业链、ETF/指数观察、工具使用方法”的角度

本期标题: {episode_title}
主选题: {topic.get('title', '')}
主选题摘要: {topic.get('summary', '')}
AI分析素材:
{analysis_text}

今日候选新闻:
{chr(10).join(news_lines)}

输出格式: 严格 JSON 数组，不要 markdown 代码块。每段格式为 {{"type":"intro|topic|tool_rec|outro","text":"...","pause_after_ms":N}}。

结构要求（按顺序9段，括号内为硬性最低字数，不够就扩写细节和案例）:
1. intro，320-420字，固定开场“大家好，欢迎收听「代码与财富」。我是你们的老朋友，一个每天用AI写代码也用AI研究投资的程序员。今天的口号是：用代码理解世界，用AI管好钱包。”然后引出话题。
2. topic，600-700字，事件背景，只讲听众必须知道的信息。
3. topic，650-750字，AI工具分析过程，必须出现“我用XX工具分析了XX”，讲清楚提问方式、拆解框架和至少2个追问。
4. topic，650-750字，商业模式/成本结构/产业链影响，避免空泛趋势判断。
5. topic，650-750字，投资观察：关联哪些公司类型、ETF/指数、财报指标或风险因子，不给买卖建议。
6. topic，650-750字，个人观点和可执行建议，落到普通程序员如何跟踪、验证、记录。
7. tool_rec，700-850字，AI工具实测，讲具体用法、提示词、优缺点、适用场景。
8. topic，500-650字，反方视角和风险清单，至少列出4个可能错判的点。
9. outro，180-240字，一句话建议 + 免责声明 + 固定结尾。

硬性质量门槛:
- JSON 中所有 text 合计必须 >= 4800 字，建议 5000 字左右；不足时不要结束，继续扩写第3、5、7、8段。
- 每段 text 不要低于对应最低字数；不要为了凑字重复同一句话。
- 必须保留 9 段，不要合并段落，不要增加第10段。

要求: 口语化，像朋友聊天；不要只复述新闻；每段之间有自然过渡；只输出 JSON 数组。"""


def strip_json_code_fence(content: str) -> str:
    content = content.strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[1]
        if content.endswith("```"):
            content = content[:-3]
    return content.strip()


def call_ainaba_json(prompt: str, api_key: str, env: dict, temperature: float = 0.8, timeout: int = 180):
    payload = json.dumps({
        "model": "gpt-4.1",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": 8000,
    }).encode("utf-8")
    req = urllib.request.Request(
        env.get("AINAIBA_API_URL", "https://api-xai.ainaibahub.com/v1").rstrip("/") + "/chat/completions",
        data=payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = json.loads(resp.read().decode("utf-8"))
    return json.loads(strip_json_code_fence(raw["choices"][0]["message"]["content"]))


MIN_SCRIPT_CHARS = 4800


def script_char_count(script: list) -> int:
    return sum(len(segment.get("text", "")) for segment in script if isinstance(segment, dict))


def validate_script_segments(script: list, min_chars: int | None = None) -> None:
    if not isinstance(script, list) or not script:
        raise RuntimeError("脚本生成结果不是非空 JSON 数组")
    for idx, segment in enumerate(script, 1):
        if not isinstance(segment, dict):
            raise RuntimeError(f"脚本第 {idx} 段不是对象")
        if not segment.get("text"):
            raise RuntimeError(f"脚本第 {idx} 段缺少 text")
        segment.setdefault("pause_after_ms", 800 if idx < len(script) else 0)
    if min_chars is not None:
        total_chars = script_char_count(script)
        if total_chars < min_chars:
            raise RuntimeError(f"脚本总字数 {total_chars} 低于最低要求 {min_chars}")


def build_expand_prompt(script: list, episode_title: str, min_chars: int = MIN_SCRIPT_CHARS) -> str:
    return f"""你是播客「代码与财富」的口播编辑。下面 JSON 脚本太短，请在保持结构不变的前提下扩写到至少 {min_chars} 字。

必须遵守:
- 只输出 JSON 数组，不要 markdown 代码块
- 段落数量、顺序、type、pause_after_ms 必须不变
- 所有 text 合计必须 >= {min_chars} 字，建议 5000-5400 字
- 优先扩写第3、5、7、8段：补充 AI 分析追问、投资观察指标、工具实测步骤、反方风险
- 不要重复原句，不要编造具体财务数字，不要荐股
- 保留“不构成投资建议”免责声明

本期标题: {episode_title}
原脚本 JSON:
{json.dumps(script, ensure_ascii=False, indent=2)}"""


def ensure_script_length(script: list, episode_title: str, api_key: str, env: dict,
                         min_chars: int = MIN_SCRIPT_CHARS) -> list:
    total_chars = script_char_count(script)
    if total_chars >= min_chars:
        return script
    expanded = call_ainaba_json(
        build_expand_prompt(script, episode_title, min_chars=min_chars),
        api_key=api_key,
        env=env,
        temperature=0.7,
        timeout=180,
    )
    validate_script_segments(expanded, min_chars=min_chars)
    if len(expanded) != len(script):
        raise RuntimeError("扩写器改变了脚本段落数量")
    for idx, (old, new) in enumerate(zip(script, expanded), 1):
        if new.get("type") != old.get("type"):
            raise RuntimeError(f"扩写器改变了第 {idx} 段 type")
        new["pause_after_ms"] = old.get("pause_after_ms", new.get("pause_after_ms", 800))
    return expanded


def build_humanize_prompt(script: list, episode_title: str) -> str:
    return f"""你是播客「代码与财富」的口播编辑。请把下面 JSON 脚本去 AI 味，但保持 JSON 数组结构完全不变。

节目人设:
- 一个用 AI 研究投资的程序员，不是财经老师，不装专家
- 说话像朋友聊天，有自己的犹豫、判断和真实操作
- 风格：直接、具体、短句多一点，允许有“我其实有点纠结”“我不敢说满”“这个地方我会更谨慎”这类真实表达

必须保留:
- 每段 type 不变
- 每段 pause_after_ms 不变
- intro 的节目名和口号不变
- outro 的免责声明“不构成投资建议”不变
- 所有事实、数字、公司名、工具名不乱改

重点处理:
- 删除“值得注意的是、反映了更广泛趋势、凸显重要性、未来充满机遇、让我们深入探讨”等 AI 套话
- 少用排比和三段式总结
- 不要百科腔，不要研报腔，不要公众号鸡汤
- 增加第一人称体验：我怎么看、我怎么用 AI 查、我会怎么做
- 句子更适合 TTS 口播，长句拆短

输出要求:
- 只输出 JSON 数组，不要 markdown 代码块
- 字段只允许 type、text、pause_after_ms
- 段落数量和顺序必须和输入一致

本期标题: {episode_title}
原脚本 JSON:
{json.dumps(script, ensure_ascii=False, indent=2)}"""


def humanize_script_segments(script: list, episode_title: str, api_key: str, env: dict) -> list:
    humanized = call_ainaba_json(
        build_humanize_prompt(script, episode_title),
        api_key=api_key,
        env=env,
        temperature=0.75,
        timeout=180,
    )
    validate_script_segments(humanized)
    if len(humanized) != len(script):
        raise RuntimeError("humanizer 改变了脚本段落数量")
    for idx, (old, new) in enumerate(zip(script, humanized), 1):
        if new.get("type") != old.get("type"):
            raise RuntimeError(f"humanizer 改变了第 {idx} 段 type")
        new["pause_after_ms"] = old.get("pause_after_ms", new.get("pause_after_ms", 800))
        new.pop("audit", None)
    return humanized


def generate_script_from_review(data: dict, episode_num: int, episode_title: str) -> str:
    env = load_runtime_env()
    api_key = env.get("AINAIBA_API_KEY")
    if not api_key:
        raise RuntimeError("缺少 AINAIBA_API_KEY")
    script = call_ainaba_json(build_script_prompt(data, episode_title), api_key=api_key, env=env)
    validate_script_segments(script)
    script = ensure_script_length(script, episode_title, api_key=api_key, env=env)
    raw_script_path = os.path.join(OUTPUT_DIR, f"ep{episode_num:02d}_script.raw.json")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(raw_script_path, "w", encoding="utf-8") as f:
        json.dump(script, f, ensure_ascii=False, indent=2)
    try:
        script = humanize_script_segments(script, episode_title, api_key=api_key, env=env)
        validate_script_segments(script, min_chars=MIN_SCRIPT_CHARS)
    except Exception as e:
        print(f"⚠️ humanizer 失败或压缩过度，使用扩写后原始脚本: {e}", file=sys.stderr)
    script_path = data.get("publish", {}).get("script_path") or os.path.join(OUTPUT_DIR, f"ep{episode_num:02d}_script.json")
    with open(script_path, "w", encoding="utf-8") as f:
        json.dump(script, f, ensure_ascii=False, indent=2)
    return script_path


def run_audio_pipeline(script_path: str, episode_num: int, title: str = "", summary: str = "") -> str:
    env = load_runtime_env()
    audio_path = os.path.join(OUTPUT_DIR, f"ep{episode_num:02d}.mp3")
    result = subprocess.run(
        [
            "python3", PIPELINE_SCRIPT, script_path, audio_path,
            "--no-rss", "--episode-num", str(episode_num),
            "--episode-title", title, "--description", summary,
            "--tts-workers", env.get("PODCAST_TTS_WORKERS", "2"),
            "--tts-timeout", env.get("PODCAST_TTS_TIMEOUT", "120"),
        ],
        cwd=WORKSPACE,
        env=env,
        text=True,
        capture_output=True,
        timeout=2400,
    )
    log_path = os.path.join(OUTPUT_DIR, f"ep{episode_num:02d}_pipeline.log")
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(result.stdout)
        f.write("\n--- STDERR ---\n")
        f.write(result.stderr)
    if result.returncode != 0:
        raise RuntimeError(f"音频管线失败，详见 {log_path}: {result.stderr[-500:]}")
    if not os.path.exists(audio_path) or os.path.getsize(audio_path) <= 0:
        raise RuntimeError("音频管线未生成有效 MP3")
    return audio_path


def publish_audio(audio_path: str, episode_num: int, episodes_dir: str = RSS_EPISODES_DIR) -> str:
    os.makedirs(episodes_dir, exist_ok=True)
    dest = os.path.join(episodes_dir, f"ep{episode_num:02d}.mp3")
    shutil.copy2(audio_path, dest)
    if os.path.getsize(dest) <= 0:
        raise RuntimeError("发布音频文件为空")
    return dest


def audio_duration(audio_path: str) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", audio_path],
        capture_output=True,
        text=True,
        check=True,
    )
    return float(result.stdout.strip())


def remove_existing_episode(channel, episode_num: int, audio_filename: str) -> None:
    for item in list(channel.findall("item")):
        ep = item.find(f"{{{ITUNES_NS}}}episode")
        enclosure = item.find("enclosure")
        same_ep = ep is not None and ep.text == str(episode_num)
        same_file = enclosure is not None and (enclosure.get("url") or "").endswith("/" + audio_filename)
        if same_ep or same_file:
            channel.remove(item)


def update_feed(episode_num: int, title: str, summary: str, audio_path: str,
                feed_path: str = RSS_FEED_PATH) -> None:
    tree = ET.parse(feed_path)
    root = tree.getroot()
    channel = root.find("channel")
    if channel is None:
        raise RuntimeError("RSS feed 缺少 channel")
    now = datetime.now(timezone(timedelta(hours=8)))
    now_str = now.strftime("%a, %d %b %Y %H:%M:%S %z")
    last_build = channel.find("lastBuildDate")
    if last_build is not None:
        last_build.text = now_str
    audio_filename = os.path.basename(audio_path)
    remove_existing_episode(channel, episode_num, audio_filename)
    item = ET.Element("item")
    ET.SubElement(item, "title").text = title
    ET.SubElement(item, f"{{{ITUNES_NS}}}title").text = title.replace(f"EP{episode_num:02d}: ", "", 1)
    ET.SubElement(item, f"{{{ITUNES_NS}}}episode").text = str(episode_num)
    ET.SubElement(item, f"{{{ITUNES_NS}}}season").text = "1"
    ET.SubElement(item, f"{{{ITUNES_NS}}}episodeType").text = "full"
    ET.SubElement(item, f"{{{ITUNES_NS}}}duration").text = str(int(audio_duration(audio_path)))
    ET.SubElement(item, f"{{{ITUNES_NS}}}summary").text = summary
    ET.SubElement(item, "description").text = f"<p>{summary}</p>"
    ET.SubElement(item, "pubDate").text = now_str
    enclosure = ET.SubElement(item, "enclosure")
    enclosure.set("url", f"{RSS_BASE_URL}/episodes/{audio_filename}")
    enclosure.set("length", str(os.path.getsize(audio_path)))
    enclosure.set("type", "audio/mpeg")
    ET.SubElement(item, "link").text = RSS_BASE_URL + "/"
    guid = ET.SubElement(item, "guid")
    guid.set("isPermaLink", "false")
    guid.text = f"ep{episode_num:02d}-{now.strftime('%Y%m%d')}"
    children = list(channel)
    insert_at = next((i for i, child in enumerate(children) if child.tag == "item"), len(children))
    channel.insert(insert_at, item)
    tree.write(feed_path, encoding="utf-8", xml_declaration=True)


def prepare_dry_run_rss_workspace() -> tuple[str, str]:
    dry_root = os.path.join(OUTPUT_DIR, "dryrun_rss")
    dry_episodes = os.path.join(dry_root, "episodes")
    os.makedirs(dry_episodes, exist_ok=True)
    dry_feed = os.path.join(dry_root, "feed.xml")
    shutil.copy2(RSS_FEED_PATH, dry_feed)
    return dry_feed, dry_episodes


def git_publish(episode_num: int, audio_path: str, dry_run: bool = False) -> str:
    rel_audio = os.path.relpath(audio_path, RSS_DIR)
    if dry_run:
        return "dry_run"
    subprocess.run(["git", "add", "feed.xml", rel_audio], cwd=RSS_DIR, check=True)
    staged = subprocess.run(
        ["git", "diff", "--cached", "--quiet", "--", "feed.xml", rel_audio],
        cwd=RSS_DIR,
    )
    if staged.returncode == 0:
        return "no_changes"
    subprocess.run(["git", "commit", "-m", f"Publish EP{episode_num:02d}"], cwd=RSS_DIR, check=True)
    subprocess.run(["git", "push", "origin", "main"], cwd=RSS_DIR, check=True)
    return "pushed"


def generate_today_content():
    """AI 自动生成今日内容"""
    print("📰 Step 1: 抓取今日新闻...")
    env = load_runtime_env()
    result = subprocess.run(
        ["python3", FETCH_SCRIPT, "--count", "5"],
        cwd=WORKSPACE,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        print(f"❌ 新闻抓取失败: {result.stderr}", file=sys.stderr)
        return False

    news_file = os.path.join(OUTPUT_DIR, "today_news.json")
    if not os.path.exists(news_file):
        print("❌ 新闻文件不存在", file=sys.stderr)
        return False
    with open(news_file, encoding="utf-8") as f:
        news = json.load(f)
    if not news:
        print("❌ 没有抓到新闻", file=sys.stderr)
        return False

    print(f"✅ 抓取到 {len(news)} 条新闻")
    best_topic = news[0]
    print(f"\n🎯 推荐选题: {best_topic['title']}")
    print(f"   来源: {best_topic['source']}")
    print(f"   分数: {best_topic['score']}")

    print(f"\n🤖 Step 2: AI 分析选题...")
    result = subprocess.run(
        ["python3", ANALYSIS_SCRIPT, "--topic", best_topic["title"], "--format", "json"],
        cwd=WORKSPACE,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        print("⚠️ AI 分析失败，使用原始新闻", file=sys.stderr)
        analysis = {"raw_text": best_topic.get("summary", "")}
    else:
        try:
            analysis = json.loads(result.stdout)
        except json.JSONDecodeError:
            analysis = {"raw_text": result.stdout}

    os.makedirs(REVIEW_DIR, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    review_file = find_today_review_file()
    review_data = {
        "date": today,
        "status": "pending",
        "news": news,
        "selected_topic": best_topic,
        "analysis": analysis,
        "created_at": datetime.now().isoformat(),
        "user_comments": "",
        "user_approved": False,
    }
    save_review_data(review_file, review_data)

    print(f"\n✅ 待审核内容已保存: {review_file}")
    print("\n" + "=" * 50)
    print("📋 请审核今日内容:")
    print("=" * 50)
    print(f"\n选题: {best_topic['title']}")
    print(f"来源: {best_topic['source']}")
    print(f"摘要: {best_topic.get('summary', '无')[:200]}...")
    if "raw_text" in analysis:
        print(f"\nAI 分析:\n{analysis['raw_text'][:500]}...")
    elif "话题背景" in analysis:
        print(f"\nAI 分析:")
        print(f"  背景: {analysis.get('话题背景', '无')[:100]}...")
        print(f"  发现: {analysis.get('核心发现', '无')[:100]}...")
        print(f"  建议: {analysis.get('可执行建议', '无')[:100]}...")
    print("\n" + "=" * 50)
    print("下一步:")
    print("  python3 review_workflow.py --review    # 查看完整内容")
    print("  python3 review_workflow.py --approve   # 确认并发布")
    print("  python3 review_workflow.py --reject    # 拒绝重新生成")
    print("=" * 50)
    return True


def review_today_content():
    """查看今日待审核内容"""
    review_file = find_today_review_file()
    if not os.path.exists(review_file):
        print("❌ 今日没有待审核内容")
        print("   请先运行: python3 review_workflow.py --generate")
        return False
    data = load_review_data(review_file)

    print("=" * 50)
    print(f"📋 今日内容审核 - {data['date']}")
    print("=" * 50)
    print(f"\n🎯 选题:")
    print(f"   标题: {data['selected_topic']['title']}")
    print(f"   来源: {data['selected_topic']['source']}")
    print(f"   分数: {data['selected_topic']['score']}")

    print(f"\n🤖 AI 分析:")
    analysis = data["analysis"]
    if "raw_text" in analysis:
        print(analysis["raw_text"])
    else:
        for key in ["话题背景", "AI分析过程", "核心发现", "个人观点", "可执行建议", "一句话总结"]:
            if key in analysis:
                print(f"\n【{key}】")
                print(analysis[key])
    if data.get("user_comments"):
        print(f"\n💬 你的评论:")
        print(data["user_comments"])
    status = "✅ 已确认" if data.get("user_approved") else "⏳ 待确认"
    print(f"\n状态: {status} / {data.get('status')}")
    if data.get("publish"):
        print(f"发布状态: {json.dumps(data['publish'], ensure_ascii=False, indent=2)}")
    print("\n" + "=" * 50)
    print("下一步:")
    print("  python3 review_workflow.py --approve   # 确认并发布")
    print("  python3 review_workflow.py --reject    # 拒绝重新生成")
    print("=" * 50)
    return True


def get_publish_paths(data: dict, dry_run: bool) -> dict:
    """Return publish state paths, isolating dry-run outputs from real publish state."""
    publish = data.setdefault("publish", {})
    if dry_run:
        return publish.setdefault("preview", {})
    publish.pop("preview", None)
    return publish


def ensure_approvable(data: dict, dry_run: bool) -> None:
    status = data.get("status")
    if dry_run:
        if status == "published":
            raise RuntimeError("内容已正式发布，拒绝重复 dry-run")
        return
    if status in {"published", "dry_run_completed"}:
        raise RuntimeError(f"当前状态为 {status}，拒绝重复正式发布；请先重新生成或清理状态")


def approve_today_content(dry_run: bool = False):
    """确认并执行发布闭环：脚本 -> 音频 -> RSS -> GitHub Pages。"""
    review_file = find_today_review_file()
    if not os.path.exists(review_file):
        print("❌ 今日没有待审核内容")
        return False

    data = load_review_data(review_file)
    try:
        ensure_approvable(data, dry_run=dry_run)
    except RuntimeError as e:
        print(f"❌ {e}", file=sys.stderr)
        return False
    episode_num = int(data.get("publish", {}).get("episode_num") or get_next_episode_number())
    title = data.get("publish", {}).get("title") or make_episode_title(data, episode_num)
    summary = data.get("publish", {}).get("summary") or make_episode_summary(data)
    data.update({
        "status": "publishing",
        "user_approved": True,
        "approved_at": data.get("approved_at") or datetime.now().isoformat(),
    })
    data.setdefault("publish", {}).update({"episode_num": episode_num, "title": title, "summary": summary})
    save_review_data(review_file, data)

    try:
        print(f"✅ 内容已确认，开始发布 EP{episode_num:02d}")
        path_state = get_publish_paths(data, dry_run=dry_run)
        script_path = path_state.get("script_path") or generate_script_from_review(data, episode_num, title)
        path_state["script_path"] = script_path
        data = mark_publish_step(review_file, data, "script_generated", script_path=script_path)

        path_state = get_publish_paths(data, dry_run=dry_run)
        audio_path = path_state.get("audio_path") or run_audio_pipeline(script_path, episode_num, title, summary)
        path_state["audio_path"] = audio_path
        data = mark_publish_step(review_file, data, "audio_rendered", audio_path=audio_path)

        target_feed = RSS_FEED_PATH
        target_episodes_dir = RSS_EPISODES_DIR
        if dry_run:
            target_feed, target_episodes_dir = prepare_dry_run_rss_workspace()

        published_audio = publish_audio(audio_path, episode_num, episodes_dir=target_episodes_dir)
        path_state = get_publish_paths(data, dry_run=dry_run)
        path_state["published_audio"] = published_audio
        data = mark_publish_step(review_file, data, "audio_published", published_audio=published_audio)

        update_feed(episode_num, title, summary, published_audio, feed_path=target_feed)
        data = mark_publish_step(review_file, data, "rss_updated", feed_path=target_feed)

        git_result = git_publish(episode_num, published_audio, dry_run=dry_run)
        data = mark_publish_step(review_file, data, "git_published", result=git_result)

        data = load_review_data(review_file)
        data["status"] = "published" if not dry_run else "dry_run_completed"
        if dry_run:
            data.pop("published_at", None)
            data["dry_run_completed_at"] = datetime.now().isoformat()
        else:
            data["published_at"] = datetime.now().isoformat()
        save_review_data(review_file, data)
        result_label = "dry-run 完成" if dry_run else "已发布"
        print(f"\n✅ EP{episode_num:02d} {result_label}: {RSS_BASE_URL}/feed.xml")
        return True
    except Exception as e:
        mark_publish_error(review_file, data, "approve", str(e))
        print(f"❌ 发布失败: {e}", file=sys.stderr)
        return False


def reject_today_content():
    """拒绝今日内容，重新生成"""
    review_file = find_today_review_file()
    if not os.path.exists(review_file):
        print("❌ 今日没有待审核内容")
        return False
    print("💬 请输入拒绝原因（可选，帮助 AI 改进）:")
    print("   （直接回车跳过）")
    comments = input("> ").strip()
    data = load_review_data(review_file)
    data["status"] = "rejected"
    data["user_approved"] = False
    data["user_comments"] = comments
    data["rejected_at"] = datetime.now().isoformat()
    save_review_data(review_file, data)
    print("\n🔄 内容已拒绝，重新生成...")
    return generate_today_content()


def main():
    import argparse
    parser = argparse.ArgumentParser(description="播客内容审核流程")
    parser.add_argument("--generate", action="store_true", help="生成今日内容")
    parser.add_argument("--review", action="store_true", help="查看待审核内容")
    parser.add_argument("--approve", action="store_true", help="确认并发布")
    parser.add_argument("--reject", action="store_true", help="拒绝重新生成")
    parser.add_argument("--dry-run", action="store_true", help="执行到 RSS 更新为止，不提交/推送 git")
    args = parser.parse_args()

    if args.generate:
        ok = generate_today_content()
    elif args.review:
        ok = review_today_content()
    elif args.approve:
        ok = approve_today_content(dry_run=args.dry_run)
    elif args.reject:
        ok = reject_today_content()
    else:
        parser.print_help()
        ok = False
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
