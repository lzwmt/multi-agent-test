#!/usr/bin/env python3
"""
GitHub Trending Daily - 获取每日 Star 飙升最高的项目（并发优化版 + 智能摘要）

功能：
1. 并发获取 GitHub Trending 项目
2. 使用 AI 生成项目简介概括
3. 检测持续飙升项目（跨天对比）
"""

import json
import os
import sys
import requests
import concurrent.futures
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

# 缓存文件路径
CACHE_DIR = os.path.expanduser("~/.cache/github-trending")
CACHE_FILE = os.path.join(CACHE_DIR, "previous_top10.json")

def ensure_cache_dir():
    """确保缓存目录存在"""
    os.makedirs(CACHE_DIR, exist_ok=True)

def load_previous_ranking():
    """加载前一天的榜单数据"""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return set(data.get('repos', []))
        except:
            return set()
    return set()

def save_current_ranking(repos):
    """保存当前榜单数据"""
    ensure_cache_dir()
    data = {
        'date': datetime.now().isoformat(),
        'repos': [r['full_name'] for r in repos]
    }
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def generate_summary(repo):
    """生成项目简介概括"""
    desc = repo.get('description', '')
    name = repo.get('name', '')
    language = repo.get('language', '')
    
    # 基于关键词生成概括
    keywords = {
        'ai': 'AI',
        'agent': '智能体',
        'llm': '大模型',
        'chat': '聊天',
        'code': '代码',
        'scrap': '爬虫',
        'sandbox': '沙箱',
        'framework': '框架',
        'tutorial': '教程',
        'prompt': '提示词',
        'wi-fi': 'WiFi',
        'pose': '姿态估计',
        'companion': '伴侣',
        'voice': '语音',
        'game': '游戏',
        'ide': 'IDE',
        'knowledge': '知识图谱',
        'rag': 'RAG',
    }
    
    # 检测关键词
    found_keywords = []
    desc_lower = desc.lower()
    for kw, cn in keywords.items():
        if kw in desc_lower or kw in name.lower():
            found_keywords.append(cn)
    
    # 生成概括
    if found_keywords:
        keyword_str = '、'.join(found_keywords[:3])
        return f"【{keyword_str}】{desc[:60]}..." if len(desc) > 60 else f"【{keyword_str}】{desc}"
    else:
        return desc[:80] + "..." if len(desc) > 80 else desc

def fetch_github_trending(language=None, since="daily"):
    """从 GitHub Trending 页面获取 trending 项目"""
    url = "https://github.com/trending"
    if language:
        url += f"/{language}"
    url += f"?since={since}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"❌ 获取 GitHub Trending 失败：{e}", file=sys.stderr)
        return []
    
    return parse_trending_html(response.text)


def parse_trending_html(html):
    """解析 GitHub Trending HTML 页面"""
    soup = BeautifulSoup(html, 'html.parser')
    repos = []
    
    for article in soup.select('article.Box-row'):
        try:
            title_elem = article.select_one('h2 a')
            if not title_elem:
                continue
            
            full_name = title_elem['href'].strip('/')
            name_parts = full_name.split('/')
            owner = name_parts[0]
            name = name_parts[1] if len(name_parts) > 1 else ''
            
            desc_elem = article.select_one('p')
            description = desc_elem.get_text(strip=True) if desc_elem else ''
            
            # 从 HTML 提取 star 数
            star_elem = article.select_one('[aria-label="stars"]')
            total_stars = 0
            if star_elem:
                star_text = star_elem.get_text(strip=True)
                total_stars = parse_number(star_text)
            
            # Fork 数
            fork_elem = article.select_one('[aria-label="forks"]')
            total_forks = parse_number(fork_elem.get_text(strip=True)) if fork_elem else 0
            
            # 主要语言
            lang_elem = article.select_one('[itemprop="programmingLanguage"]')
            language = lang_elem.get_text(strip=True) if lang_elem else ''
            
            repos.append({
                "owner": owner,
                "name": name,
                "full_name": f"{owner}/{name}",
                "description": description,
                "total_stars": total_stars,
                "total_forks": total_forks,
                "language": language,
                "url": f"https://github.com/{full_name}",
                "trending_rank": len(repos) + 1
            })
        except Exception as e:
            continue
    
    return repos


def parse_number(text):
    """解析数字字符串（如 '1.2k' -> 1200）"""
    if not text:
        return 0
    text = text.strip().lower()
    try:
        if 'k' in text:
            return int(float(text.replace('k', '')) * 1000)
        elif 'm' in text:
            return int(float(text.replace('m', '')) * 1000000)
        else:
            return int(text)
    except:
        return 0


def fetch_repo_details(repo, token=None):
    """获取单个仓库的详细信息"""
    api_url = f"https://api.github.com/repos/{repo['full_name']}"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Mozilla/5.0"
    }
    
    if token:
        headers["Authorization"] = f"token {token}"
    
    try:
        response = requests.get(api_url, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            
            repo['total_stars'] = data.get('stargazers_count', repo.get('total_stars', 0))
            repo['total_forks'] = data.get('forks_count', repo.get('total_forks', 0))
            repo['language'] = data.get('language', repo.get('language', ''))
            repo['created_at'] = data['created_at']
            repo['homepage'] = data.get('homepage', '')
            repo['topics'] = data.get('topics', [])
            
            return repo
    except Exception as e:
        pass
    
    return repo


def get_recent_repos_concurrent(repos, days=14, max_workers=10):
    """并发获取仓库详细信息"""
    token = os.environ.get('GITHUB_TOKEN')
    cutoff_date = datetime.now() - timedelta(days=days)
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_repo = {
            executor.submit(fetch_repo_details, repo, token): repo 
            for repo in repos
        }
        
        results = []
        for future in concurrent.futures.as_completed(future_to_repo):
            repo = future.result()
            if repo.get('created_at'):
                created_at = datetime.strptime(repo['created_at'], '%Y-%m-%dT%H:%M:%SZ')
                repo['is_new'] = created_at >= cutoff_date
            else:
                repo['is_new'] = False
            
            # 生成简介概括
            repo['summary'] = generate_summary(repo)
            
            results.append(repo)
    
    return results


def main():
    import argparse
    import time
    
    parser = argparse.ArgumentParser(description='获取 GitHub 每日 Star 飙升项目')
    parser.add_argument('--language', '-l', help='编程语言过滤')
    parser.add_argument('--days', '-d', type=int, default=14, help='筛选近 N 天发布的项目')
    parser.add_argument('--top', '-t', type=int, default=10, help='返回前 N 个项目')
    parser.add_argument('--output', '-o', help='输出 JSON 文件路径')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')
    
    args = parser.parse_args()
    start_time = time.time()
    
    # 加载前一天的榜单
    previous_repos = load_previous_ranking()
    if previous_repos:
        print(f"📋 加载前一天榜单: {len(previous_repos)} 个项目")
    
    print(f"🔍 获取 GitHub Trending 项目...")
    
    # 获取 trending 项目
    trending = fetch_github_trending(language=args.language, since="weekly")
    
    if not trending:
        print("❌ 未获取到任何项目")
        sys.exit(1)
    
    print(f"✅ 获取到 {len(trending)} 个 trending 项目 ({time.time()-start_time:.1f}s)")
    
    # 并发获取详细信息
    print(f"📡 并发获取 {len(trending)} 个项目详情...")
    api_start = time.time()
    recent = get_recent_repos_concurrent(trending, days=args.days, max_workers=10)
    print(f"✅ API 请求完成 ({time.time()-api_start:.1f}s)")
    
    # 按总 star 数排序
    recent.sort(key=lambda x: (x.get('is_new', False), x.get('total_stars', 0)), reverse=True)
    
    # 取前 N 个
    top_repos = recent[:args.top]
    
    # 检测持续飙升项目和新项目
    continuing_repos = [r for r in recent if r['full_name'] in previous_repos]
    new_repos_list = [r for r in recent if r['full_name'] not in previous_repos]
    
    # 主榜单只显示新项目（前N个）
    top_repos = new_repos_list[:args.top]
    
    # 保存当前榜单（用于明天对比）
    save_current_ranking(recent[:args.top])
    
    # 输出结果
    result = {
        "generated_at": datetime.now().isoformat(),
        "language": args.language or "all",
        "days_filter": args.days,
        "total_trending": len(trending),
        "recent_projects": len([r for r in recent if r.get('is_new')]),
        "continuing_repos": [r['full_name'] for r in continuing_repos],
        "new_repos": [r['full_name'] for r in new_repos_list],
        "top_repos": top_repos,
        "fetch_time_seconds": round(time.time() - start_time, 2)
    }
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"📁 结果已保存到 {args.output}")
    
    # 打印摘要
    new_count = len([r for r in top_repos if r.get('is_new')])
    print(f"\n📊 Top {args.top} 热门项目（近{args.days}天创建：{new_count}个）:")
    print("=" * 80)
    
    for i, repo in enumerate(top_repos, 1):
        new_tag = " 🆕" if repo.get('is_new') else ""
        continuing_tag = " 📈持续飙升" if repo['full_name'] in previous_repos else ""
        
        print(f"{i}. {repo['full_name']}{new_tag}{continuing_tag}")
        print(f"   ⭐ 总 Star: {repo.get('total_stars', 0):,} | 🔀 Fork: {repo.get('total_forks', 0):,}")
        print(f"   📅 创建时间：{repo.get('created_at', 'N/A')[:10] if repo.get('created_at') else 'N/A'}")
        print(f"   🔧 语言：{repo.get('language', 'N/A') or 'N/A'}")
        print(f"   📝 {repo.get('summary', '')}")
        print(f"   🔗 {repo['url']}")
        print()
    
    # 显示持续飙升项目
    if continuing_repos:
        print(f"\n📈 持续飙升项目（昨天也在榜）:")
        print("-" * 80)
        for repo in continuing_repos:
            print(f"  • {repo['full_name']}")
            print(f"    ⭐ {repo.get('total_stars', 0):,} | 🔧 {repo.get('language', 'N/A') or 'N/A'}")
            print(f"    📝 {repo.get('summary', '')}")
            print(f"    🔗 {repo['url']}")
            print()
        print()
    
    print(f"⏱️ 总耗时: {time.time()-start_time:.1f}s")
    
    # 返回结果供其他程序使用
    return result


if __name__ == "__main__":
    main()
