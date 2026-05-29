import json, pathlib

html_path = pathlib.Path("/root/workspace/wechat-oa/output/articles/20260528_fingerprint_regeneration.wechat.html")
html_content = html_path.read_text(encoding="utf-8")

draft = {
    "articles": [
        {
            "title": "花六千美金削掉指纹，结果它自己又长回来了",
            "author": "历史冷知识",
            "digest": "指纹被破坏后居然能原样再生，这个看似简单的现象背后藏着皮肤干细胞的精密记忆系统。从黑帮酸蚀指纹到科学家自己做实验，人类花了近百年才搞明白这件事。",
            "content": html_content,
            "thumb_media_id": "hhSZwwwIqs3SvJXN9JDYu6uPUkc0BdTUnIwesegL9SIdrST4ISKg9FfeH9te3VX-",
            "show_cover_pic": 1
        }
    ]
}

draft_path = pathlib.Path("/root/workspace/wechat-oa/output/articles/20260528_draft.json")
draft_path.write_text(json.dumps(draft, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Draft JSON written to {draft_path}")
