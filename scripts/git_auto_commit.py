#!/usr/bin/env python3
"""
Git 自动提交工具
自动提交 memory 目录的变更到 Git
"""

import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path

WORKSPACE_DIR = Path("/root/.openclaw/workspace")
MEMORY_DIR = WORKSPACE_DIR / "memory"
SOUL_MD = WORKSPACE_DIR / "SOUL.md"
MEMORY_MD = WORKSPACE_DIR / "MEMORY.md"


def run_git_command(args: list, cwd: Path = None) -> tuple:
    """执行 Git 命令"""
    if cwd is None:
        cwd = WORKSPACE_DIR
    
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr


def check_git_repo() -> bool:
    """检查是否是 Git 仓库"""
    success, _ = run_git_command(["rev-parse", "--git-dir"])
    return success


def get_changed_files() -> dict:
    """获取变更的文件列表"""
    success, output = run_git_command(["status", "--porcelain"])
    
    if not success:
        return {}
    
    changes = {
        "memory": [],
        "soul": False,
        "memory_md": False,
        "other": []
    }
    
    for line in output.strip().split("\n"):
        if not line:
            continue
        
        status = line[:2]
        filepath = line[3:].strip()
        
        if filepath.startswith("memory/"):
            changes["memory"].append(filepath)
        elif filepath == "SOUL.md":
            changes["soul"] = True
        elif filepath == "MEMORY.md":
            changes["memory_md"] = True
        else:
            changes["other"].append(filepath)
    
    return changes


def commit_memory_files(message: str = None) -> dict:
    """提交 memory 相关文件"""
    result = {
        "success": False,
        "committed": [],
        "message": ""
    }
    
    changes = get_changed_files()
    
    # 检查是否有变更
    files_to_commit = []
    files_to_commit.extend(changes["memory"])
    
    if changes["soul"]:
        files_to_commit.append("SOUL.md")
    
    if changes["memory_md"]:
        files_to_commit.append("MEMORY.md")
    
    if not files_to_commit:
        result["message"] = "No changes to commit"
        return result
    
    # 添加文件
    for filepath in files_to_commit:
        success, _ = run_git_command(["add", filepath])
        if not success:
            result["message"] = f"Failed to add {filepath}"
            return result
    
    # 生成提交信息
    if message is None:
        today = datetime.now().strftime("%Y-%m-%d")
        time = datetime.now().strftime("%H:%M")
        
        if len(changes["memory"]) == 1:
            msg = f"Update memory: {Path(changes['memory'][0]).name} ({today})"
        else:
            msg = f"Update memory files: {len(changes['memory'])} files ({today} {time})"
        
        if changes["soul"]:
            msg += " + SOUL.md"
        if changes["memory_md"]:
            msg += " + MEMORY.md"
    else:
        msg = message
    
    # 提交
    success, output = run_git_command(["commit", "-m", msg])
    
    if success:
        result["success"] = True
        result["committed"] = files_to_commit
        result["message"] = msg
        result["hash"] = get_last_commit_hash()
    else:
        result["message"] = f"Commit failed: {output}"
    
    return result


def get_last_commit_hash() -> str:
    """获取最后一次提交的哈希"""
    success, output = run_git_command(["rev-parse", "--short", "HEAD"])
    return output.strip() if success else "unknown"


def get_commit_log(days: int = 7) -> list:
    """获取最近提交历史"""
    success, output = run_git_command([
        "log", "--oneline", "--since", f"{days} days ago",
        "--", "memory/", "SOUL.md", "MEMORY.md"
    ])
    
    if not success:
        return []
    
    commits = []
    for line in output.strip().split("\n"):
        if line:
            parts = line.split(" ", 1)
            if len(parts) == 2:
                commits.append({
                    "hash": parts[0],
                    "message": parts[1]
                })
    
    return commits


def auto_commit() -> dict:
    """自动提交主函数"""
    if not check_git_repo():
        return {
            "success": False,
            "message": "Not a git repository"
        }
    
    return commit_memory_files()


def test():
    """测试功能"""
    print("=" * 60)
    print("Git 自动提交测试")
    print("=" * 60)
    
    # 1. 检查 Git 仓库
    print("\n1. 检查 Git 仓库...")
    if check_git_repo():
        print("   ✅ 是 Git 仓库")
    else:
        print("   ❌ 不是 Git 仓库")
        return
    
    # 2. 获取变更文件
    print("\n2. 检查变更文件...")
    changes = get_changed_files()
    print(f"   Memory 文件: {len(changes['memory'])} 个")
    for f in changes['memory'][:5]:
        print(f"      - {f}")
    print(f"   SOUL.md: {'有变更' if changes['soul'] else '无变更'}")
    print(f"   MEMORY.md: {'有变更' if changes['memory_md'] else '无变更'}")
    print(f"   其他文件: {len(changes['other'])} 个")
    
    # 3. 提交
    print("\n3. 执行自动提交...")
    result = auto_commit()
    
    if result["success"]:
        print(f"   ✅ 提交成功")
        print(f"      提交信息: {result['message']}")
        print(f"      提交哈希: {result['hash']}")
        print(f"      提交文件: {len(result['committed'])} 个")
        for f in result['committed']:
            print(f"         - {f}")
    else:
        print(f"   ℹ️ {result['message']}")
    
    # 4. 显示提交历史
    print("\n4. 最近提交历史...")
    commits = get_commit_log(days=7)
    for commit in commits[:5]:
        print(f"   {commit['hash']}: {commit['message']}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        test()
    elif len(sys.argv) > 1 and sys.argv[1] == "--commit":
        result = auto_commit()
        print(result["message"])
        sys.exit(0 if result["success"] else 1)
    else:
        print("用法:")
        print("  python3 git_auto_commit.py --test    # 测试")
        print("  python3 git_auto_commit.py --commit  # 执行提交")
