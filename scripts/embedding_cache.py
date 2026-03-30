#!/usr/bin/env python3
"""
Embedding Cache for Memory Search
缓存 memory 文件的嵌入向量，减少 Gemini API 调用
"""

import os
import sys
import json
import hashlib
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Tuple

# 配置
WORKSPACE_DIR = Path("/root/.openclaw/workspace")
MEMORY_DIR = WORKSPACE_DIR / "memory"
CACHE_DB = WORKSPACE_DIR / ".cache" / "embedding_cache.db"


class EmbeddingCache:
    def __init__(self, db_path: Path = CACHE_DB):
        self.db_path = db_path
        self._ensure_db()
    
    def _ensure_db(self):
        """确保数据库和表存在"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS embedding_cache (
                file_path TEXT PRIMARY KEY,
                content_hash TEXT NOT NULL,
                embedding TEXT NOT NULL,
                file_size INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_hash ON embedding_cache(content_hash)
        """)
        conn.commit()
        conn.close()
    
    def _get_file_hash(self, filepath: Path) -> str:
        """计算文件 SHA256 哈希"""
        with open(filepath, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
    
    def get_cached(self, file_path: Path, file_hash: str) -> Optional[List[float]]:
        """获取缓存的嵌入向量"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            "SELECT embedding FROM embedding_cache WHERE file_path=? AND content_hash=?",
            (str(file_path), file_hash)
        )
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return json.loads(row[0])
        return None
    
    def cache_embedding(self, file_path: Path, file_hash: str, 
                        embedding: List[float], file_size: int = 0):
        """缓存嵌入向量"""
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            """INSERT OR REPLACE INTO embedding_cache 
               (file_path, content_hash, embedding, file_size, updated_at)
               VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)""",
            (str(file_path), file_hash, json.dumps(embedding), file_size)
        )
        conn.commit()
        conn.close()
    
    def get_stats(self) -> dict:
        """获取缓存统计"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("SELECT COUNT(*), SUM(file_size) FROM embedding_cache")
        count, total_size = cursor.fetchone()
        conn.close()
        
        return {
            "cached_files": count or 0,
            "total_size_bytes": total_size or 0,
            "db_path": str(self.db_path)
        }
    
    def clear_cache(self):
        """清空缓存"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("DELETE FROM embedding_cache")
        conn.commit()
        conn.close()
        print("✅ 缓存已清空")


def test_cache():
    """测试缓存功能"""
    print("=" * 60)
    print("Embedding Cache 测试")
    print("=" * 60)
    
    cache = EmbeddingCache()
    
    # 1. 检查 memory 目录
    print(f"\n📁 Memory 目录: {MEMORY_DIR}")
    if not MEMORY_DIR.exists():
        print("❌ Memory 目录不存在")
        return
    
    # 2. 列出所有 memory 文件
    memory_files = list(MEMORY_DIR.glob("*.md"))
    print(f"📄 找到 {len(memory_files)} 个 memory 文件")
    
    # 3. 测试缓存命中/未命中
    print("\n🧪 测试缓存机制:")
    
    test_results = []
    for i, file_path in enumerate(memory_files[:5], 1):  # 测试前5个文件
        print(f"\n  [{i}] {file_path.name}")
        
        # 计算文件哈希
        file_hash = cache._get_file_hash(file_path)
        file_size = file_path.stat().st_size
        
        # 尝试获取缓存
        cached = cache.get_cached(file_path, file_hash)
        
        if cached:
            print(f"      ✅ 缓存命中 (向量维度: {len(cached)})")
            test_results.append("hit")
        else:
            print(f"      📝 缓存未命中，模拟生成嵌入...")
            # 模拟嵌入向量 (实际应调用 Gemini API)
            mock_embedding = [0.1] * 768  # Gemini embedding-001 是 768 维
            cache.cache_embedding(file_path, file_hash, mock_embedding, file_size)
            print(f"      ✅ 已缓存 (向量维度: {len(mock_embedding)})")
            test_results.append("miss")
    
    # 4. 再次测试缓存命中
    print("\n🔄 第二次查询 (应全部命中):")
    hit_count = 0
    for file_path in memory_files[:5]:
        file_hash = cache._get_file_hash(file_path)
        cached = cache.get_cached(file_path, file_hash)
        if cached:
            hit_count += 1
    
    print(f"   缓存命中率: {hit_count}/5 ({hit_count*20}%)")
    
    # 5. 显示统计
    print("\n📊 缓存统计:")
    stats = cache.get_stats()
    print(f"   缓存文件数: {stats['cached_files']}")
    print(f"   总大小: {stats['total_size_bytes'] / 1024:.2f} KB")
    print(f"   数据库: {stats['db_path']}")
    
    # 6. 验证数据库内容
    print("\n🔍 数据库内容验证:")
    conn = sqlite3.connect(cache.db_path)
    cursor = conn.execute("SELECT file_path, content_hash, file_size FROM embedding_cache LIMIT 5")
    rows = cursor.fetchall()
    conn.close()
    
    for row in rows:
        path, hash_prefix, size = row
        print(f"   - {Path(path).name}: {hash_prefix[:16]}... ({size} bytes)")
    
    print("\n" + "=" * 60)
    print("✅ 测试完成")
    print("=" * 60)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--clear":
        cache = EmbeddingCache()
        cache.clear_cache()
    else:
        test_cache()
