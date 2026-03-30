#!/usr/bin/env node
/**
 * Smart Search - 智能路由搜索
 * 
 * 策略：
 * 1. 简单查询 → Tavily (API，快速结构化)
 * 2. 需要实时/动态内容 → Lightpanda (浏览器渲染)
 * 3. Tavily 失败 → 回退到 Lightpanda
 */

import { execSync } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));

// 解析参数
const args = process.argv.slice(2);
const queryIndex = args.findIndex(arg => !arg.startsWith('--'));
const query = queryIndex >= 0 ? args[queryIndex] : '';

const options = {
  count: 10,
  engine: 'auto', // auto, tavily, lightpanda
  fallback: true
};

for (let i = 0; i < args.length; i++) {
  if (args[i] === '--count' || args[i] === '-n') {
    options.count = parseInt(args[i + 1]) || 10;
    i++;
  }
  if (args[i] === '--engine') {
    options.engine = args[i + 1] || 'auto';
    i++;
  }
  if (args[i] === '--no-fallback') {
    options.fallback = false;
  }
}

if (!query) {
  console.error('Usage: search-v2.js <query> [--count N] [--engine auto|tavily|lightpanda] [--no-fallback]');
  process.exit(1);
}

// 判断是否需要浏览器渲染
function needsBrowser(query) {
  const browserKeywords = [
    '实时', '动态', '价格', '股价', '天气', '当前',
    'real-time', 'live', 'current price', 'stock', 'weather now'
  ];
  return browserKeywords.some(kw => query.toLowerCase().includes(kw.toLowerCase()));
}

// Tavily 搜索
async function searchTavily(query, count) {
  const tavilyScript = join(__dirname, '../skills/tavily-tool/scripts/tavily_search.js');
  
  const result = execSync(
    `node "${tavilyScript}" --query "${query}" --max_results ${count}`,
    { encoding: 'utf8', timeout: 30000 }
  );
  
  const data = JSON.parse(result);
  
  return {
    success: true,
    query: data.query || query,
    results: data.results?.map(r => ({
      title: r.title || '',
      url: r.url || '',
      description: r.content || '',
      source: new URL(r.url || 'http://localhost').hostname
    })) || [],
    response_time: data.response_time || 0,
    engine: 'tavily'
  };
}

// Lightpanda 搜索
async function searchLightpanda(query, count) {
  const lightpandaScript = join(__dirname, 'lightpanda-search.js');
  
  const result = execSync(
    `node "${lightpandaScript}" "${query}" ${count}`,
    { encoding: 'utf8', timeout: 60000 }
  );
  
  const data = JSON.parse(result);
  
  return {
    ...data,
    engine: 'lightpanda'
  };
}

// 主逻辑
async function main() {
  const startTime = Date.now();
  let result;
  let usedEngine;
  
  // 决定使用哪个引擎
  if (options.engine === 'lightpanda' || (options.engine === 'auto' && needsBrowser(query))) {
    usedEngine = 'lightpanda';
    console.error(`🔍 [${usedEngine}] ${query}`);
    
    try {
      result = await searchLightpanda(query, options.count);
    } catch (error) {
      if (options.fallback) {
        console.error(`⚠️ Lightpanda failed, falling back to Tavily...`);
        usedEngine = 'tavily (fallback)';
        result = await searchTavily(query, options.count);
      } else {
        throw error;
      }
    }
  } else {
    usedEngine = 'tavily';
    console.error(`🔍 [${usedEngine}] ${query}`);
    
    try {
      result = await searchTavily(query, options.count);
    } catch (error) {
      if (options.fallback) {
        console.error(`⚠️ Tavily failed, falling back to Lightpanda...`);
        usedEngine = 'lightpanda (fallback)';
        result = await searchLightpanda(query, options.count);
      } else {
        throw error;
      }
    }
  }
  
  const totalTime = ((Date.now() - startTime) / 1000).toFixed(2);
  
  const output = {
    ...result,
    engine: usedEngine,
    total_time: `${totalTime}s`,
    strategy: options.engine
  };
  
  console.log(JSON.stringify(output, null, 2));
}

main().catch(error => {
  console.error(JSON.stringify({
    success: false,
    query,
    error: error.message
  }));
  process.exit(1);
});
