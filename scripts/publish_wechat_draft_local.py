#!/usr/bin/env python3
import argparse
import json
import pathlib
import subprocess
import sys
import tempfile

import yaml


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, capture_output=True)


def split_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---\n"):
        return {}, text
    parts = text.split("\n---\n", 1)
    if len(parts) != 2:
        return {}, text
    raw_meta = parts[0][4:]
    body = parts[1]
    try:
        data = yaml.safe_load(raw_meta) or {}
        if not isinstance(data, dict):
            data = {}
    except yaml.YAMLError:
        data = {}
    return data, body


def first_heading(markdown_text: str) -> str | None:
    for line in markdown_text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return None


def get_metadata(markdown_path: pathlib.Path) -> dict:
    raw_text = markdown_path.read_text(encoding="utf-8")
    metadata, body = split_frontmatter(raw_text)
    title = str(metadata.get("title") or first_heading(body) or markdown_path.stem)
    author = str(metadata.get("author") or "")
    digest = str(metadata.get("digest") or metadata.get("summary") or metadata.get("description") or "")
    return {"title": title, "author": author, "digest": digest}


def upload_cover(md2wechat_bin: str, cover_path: pathlib.Path) -> str:
    result = run([md2wechat_bin, "upload_image", str(cover_path), "--json"])
    if result.returncode != 0:
        raise RuntimeError(f"upload_image failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")
    payload = json.loads(result.stdout)
    media_id = payload.get("data", {}).get("media_id") or payload.get("media_id")
    if not media_id:
        raise RuntimeError(f"media_id missing in upload response:\n{result.stdout}")
    return media_id


def convert_local(markdown_path: pathlib.Path, html_path: pathlib.Path, converter_path: pathlib.Path, theme: str) -> None:
    result = run([
        sys.executable,
        str(converter_path),
        str(markdown_path),
        "-o",
        str(html_path),
        "--theme",
        theme,
    ])
    if result.returncode != 0:
        raise RuntimeError(f"local convert failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")


def create_draft_json(html_path: pathlib.Path, metadata: dict, cover_media_id: str, draft_json_path: pathlib.Path) -> None:
    html_content = html_path.read_text(encoding="utf-8")
    payload = {
        "articles": [
            {
                "title": metadata["title"],
                "author": metadata["author"],
                "digest": metadata["digest"],
                "content": html_content,
                "thumb_media_id": cover_media_id,
                "show_cover_pic": 1,
            }
        ]
    }
    draft_json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def create_draft(md2wechat_bin: str, draft_json_path: pathlib.Path) -> dict:
    result = run([md2wechat_bin, "create_draft", str(draft_json_path), "--json"])
    if result.returncode != 0:
        raise RuntimeError(f"create_draft failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")
    return json.loads(result.stdout)


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish Markdown to WeChat draft using local HTML conversion.")
    parser.add_argument("markdown", help="Input Markdown file")
    parser.add_argument("--cover", required=True, help="Cover image path for WeChat draft")
    parser.add_argument("--md2wechat-bin", default="md2wechat", help="Path to md2wechat binary")
    parser.add_argument(
        "--converter",
        default="scripts/local_md_to_wechat.py",
        help="Path to local markdown-to-html converter",
    )
    parser.add_argument(
        "--theme",
        choices=["minimal", "warm", "dark-blue"],
        default="minimal",
        help="Local HTML theme preset",
    )
    parser.add_argument(
        "--keep-files",
        action="store_true",
        help="Keep generated HTML and draft JSON files in the working directory",
    )
    args = parser.parse_args()

    markdown_path = pathlib.Path(args.markdown)
    cover_path = pathlib.Path(args.cover)
    converter_path = pathlib.Path(args.converter)

    if not markdown_path.exists():
        print(f"Markdown file not found: {markdown_path}", file=sys.stderr)
        return 1
    if not cover_path.exists():
        print(f"Cover image not found: {cover_path}", file=sys.stderr)
        return 1
    if not converter_path.exists():
        print(f"Converter script not found: {converter_path}", file=sys.stderr)
        return 1

    metadata = get_metadata(markdown_path)
    workdir = markdown_path.parent if args.keep_files else pathlib.Path(tempfile.mkdtemp(prefix="wechat-draft-"))
    html_path = workdir / f"{markdown_path.stem}.wechat.html"
    draft_json_path = workdir / f"{markdown_path.stem}.draft.json"

    convert_local(markdown_path, html_path, converter_path, args.theme)
    cover_media_id = upload_cover(args.md2wechat_bin, cover_path)
    create_draft_json(html_path, metadata, cover_media_id, draft_json_path)
    response = create_draft(args.md2wechat_bin, draft_json_path)

    output = {
        "html_file": str(html_path),
        "draft_json": str(draft_json_path),
        "cover_media_id": cover_media_id,
        "draft_response": response,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
