#!/usr/bin/env node
/**
 * Smart Search Optimized - 智能路由搜索（内存优化版）
 * 
 * 优化特性：
 * 1. 内存监控和限制
 * 2. 进程完全退出，无残留
 * 3. 资源清理（关闭连接、释放缓存）
 * 4. 限制并发请求数
 * 5. 超时机制
 * 6. 流式处理替代全量加载
 * 7. 子进程管理
 * 
 * 策略：
 * 1. 简单查询 → Tavily (API，快速结构化)
 * 2. 需要实时/动态内容 → Lightpanda (浏览器渲染)
 * 3. Tavily 失败 → 回退到 Lightpanda
 */

import { spawn } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));

// ============ 配置常量 ============
const CONFIG = {
  // 内存限制 (MB)
  MEMORY_LIMIT_MB: 512,
  // 内存监控间隔 (ms)
  MEMORY_CHECK_INTERVAL: 5000,
  // 并发限制
  MAX_CONCURRENT: 2,
  // 超时配置
  TIMEOUT: {
    TAVILY: 30000,
    LIGHTPANDA: 60000,
    PROCESS_KILL: 5000
  },
  // 流式处理缓冲区大小
  STREAM_BUFFER_SIZE: 16384, // 16KB
};

// ============ 内存监控 ============
class MemoryMonitor {
  constructor(limitMB = CONFIG.MEMORY_LIMIT_MB) {
    this.limitMB = limitMB;
    this.checkInterval = null;
    this.peakMemory = 0;
  }

  start() {
    this.checkInterval = setInterval(() => {
      const usage = process.memoryUsage();
      const heapUsedMB = Math.round(usage.heapUsed / 1024 / 1024);
      const rssMB = Math.round(usage.rss / 1024 / 1024);
      
      this.peakMemory = Math.max(this.peakMemory, rssMB);
      
      if (rssMB > this.limitMB) {
        console.error(`⚠️ Memory limit exceeded: ${rssMB}MB > ${this.limitMB}MB`);
        this.stop();
        process.exit(1);
      }
    }, CONFIG.MEMORY_CHECK_INTERVAL);
  }

  stop() {
    if (this.checkInterval) {
      clearInterval(this.checkInterval);
      this.checkInterval = null;
    }
  }

  getStats() {
    const usage = process.memoryUsage();
    return {
      heapUsed: Math.round(usage.heapUsed / 1024 / 1024),
      heapTotal: Math.round(usage.heapTotal / 1024 / 1024),
      rss: Math.round(usage.rss / 1024 / 1024),
      external: Math.round(usage.external / 1024 / 1024),
      peak: this.peakMemory
    };
  }
}

// ============ 子进程管理器 ============
class ProcessManager {
  constructor() {
    this.processes = new Set();
    this.timers = new Set();
  }

  add(proc, timeoutMs = CONFIG.TIMEOUT.PROCESS_KILL) {
    this.processes.add(proc);
    
    // 设置超时自动终止
    const timer = setTimeout(() => {
      this.kill(proc);
    }, timeoutMs);
    
    this.timers.add(timer);
    
    proc.on('exit', () => {
      this.processes.delete(proc);
      clearTimeout(timer);
      this.timers.delete(timer);
    });
    
    return proc;
  }

  kill(proc, signal = 'SIGTERM') {
    if (!proc.killed && proc.exitCode === null) {
      proc.kill(signal);
      
      // 强制终止
      setTimeout(() => {
        if (!proc.killed && proc.exitCode === null) {
          proc.kill('SIGKILL');
        }
      }, CONFIG.TIMEOUT.PROCESS_KILL);
    }
  }

  killAll(signal = 'SIGTERM') {
    for (const proc of this.processes) {
      this.kill(proc, signal);
    }
  }

  cleanup() {
    this.killAll('SIGTERM');
    for (const timer of this.timers) {
      clearTimeout(timer);
    }
    this.processes.clear();
    this.timers.clear();
  }
}

// ============ 流式执行器 ============
class StreamExecutor {
  constructor(processManager) {
    this.processManager = processManager;
  }

  async execute(command, args, options = {}) {
    const { timeout = 30000, bufferSize = CONFIG.STREAM_BUFFER_SIZE } = options;
    
    return new Promise((resolve, reject) => {
      const proc = spawn(command, args, {
        stdio: ['ignore', 'pipe', 'pipe'],
        detached: false
      });
      
      this.processManager.add(proc, timeout + CONFIG.TIMEOUT.PROCESS_KILL);
      
      let stdout = '';
      let stderr = '';
      let killed = false;
      
      // 超时处理
      const timeoutTimer = setTimeout(() => {
        killed = true;
        this.processManager.kill(proc, 'SIGTERM');
        reject(new Error(`Process timeout after ${timeout}ms`));
      }, timeout);
      
      // 流式读取 stdout
      proc.stdout.setEncoding('utf8');
      proc.stdout.on('data', (chunk) => {
        if (stdout.length < bufferSize) {
          stdout += chunk;
        }
      });
      
      // 流式读取 stderr
      proc.stderr.setEncoding('utf8');
      proc.stderr.on('data', (chunk) => {
        stderr += chunk;
      });
      
      proc.on('error', (error) => {
        clearTimeout(timeoutTimer);
        reject(error);
      });
      
      proc.on('exit', (code, signal) => {
        clearTimeout(timeoutTimer);
        
        if (killed) return;
        
        if (code === 0) {
          resolve({ stdout, stderr });
        } else {
          reject(new Error(`Process exited with code ${code}: ${stderr || stdout}`));
        }
      });
    });
  }
}

// ============ 并发控制器 ============
class ConcurrencyLimiter {
  constructor(maxConcurrent = CONFIG.MAX_CONCURRENT) {
    this.maxConcurrent = maxConcurrent;
    this.running = 0;
    this.queue = [];
  }

  async acquire() {
    if (this.running < this.maxConcurrent) {
      this.running++;
      return;
    }
    
    return new Promise(resolve => {
      this.queue.push(resolve);
    });
  }

  release() {
    this.running--;
    if (this.queue.length > 0) {
      const next = this.queue.shift();
      this.running++;
      next();
    }
  }

  async run(fn) {
    await this.acquire();
    try {
      return await fn();
    } finally {
      this.release();
    }
  }
}

// ============ 资源清理器 ============
class ResourceCleaner {
  constructor() {
    this.resources = [];
    this.cleaned = false;
  }

  add(cleanupFn, name = 'unnamed') {
    this.resources.push({ fn: cleanupFn, name });
  }

  async cleanup() {
    if (this.cleaned) return;
    this.cleaned = true;
    
    const errors = [];
    
    // 逆序清理（LIFO）
    for (let i = this.resources.length - 1; i >= 0; i--) {
      const { fn, name } = this.resources[i];
      try {
        await fn();
      } catch (error) {
        errors.push({ name, error: error.message });
      }
    }
    
    this.resources = [];
    
    if (errors.length > 0) {
      console.error('Cleanup errors:', errors);
    }
  }
}

// ============ 主搜索逻辑 ============
class SmartSearch {
  constructor() {
    this.memoryMonitor = new MemoryMonitor();
    this.processManager = new ProcessManager();
    this.streamExecutor = new StreamExecutor(this.processManager);
    this.concurrencyLimiter = new ConcurrencyLimiter();
    this.resourceCleaner = new ResourceCleaner();
    
    // 启动内存监控
    this.memoryMonitor.start();
    
    // 注册清理
    this.resourceCleaner.add(() => this.memoryMonitor.stop(), 'memoryMonitor');
    this.resourceCleaner.add(() => this.processManager.cleanup(), 'processManager');
    
    // 进程退出处理
    this.setupExitHandlers();
  }

  setupExitHandlers() {
    const cleanup = async () => {
      await this.resourceCleaner.cleanup();
      process.exit(0);
    };
    
    process.on('SIGTERM', cleanup);
    process.on('SIGINT', cleanup);
    process.on('exit', () => this.resourceCleaner.cleanup());
    
    // 未捕获异常处理
    process.on('uncaughtException', async (error) => {
      console.error('Uncaught Exception:', error);
      await this.resourceCleaner.cleanup();
      process.exit(1);
    });
    
    process.on('unhandledRejection', async (reason) => {
      console.error('Unhandled Rejection:', reason);
      await this.resourceCleaner.cleanup();
      process.exit(1);
    });
  }

  // 判断是否需要浏览器渲染
  needsBrowser(query) {
    const browserKeywords = [
      '实时', '动态', '价格', '股价', '天气', '当前',
      'real-time', 'live', 'current price', 'stock', 'weather now'
    ];
    return browserKeywords.some(kw => query.toLowerCase().includes(kw.toLowerCase()));
  }

  // Tavily 搜索（流式执行）
  async searchTavily(query, count) {
    const tavilyScript = join(__dirname, '../skills/tavily-tool/scripts/tavily_search.js');
    
    return this.concurrencyLimiter.run(async () => {
      const { stdout } = await this.streamExecutor.execute('node', [
        tavilyScript,
        '--query', query,
        '--max_results', String(count)
      ], { timeout: CONFIG.TIMEOUT.TAVILY });
      
      const data = JSON.parse(stdout);
      
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
    });
  }

  // Lightpanda 搜索（流式执行）
  async searchLightpanda(query, count) {
    const lightpandaScript = join(__dirname, 'lightpanda-search-optimized.js');
    
    return this.concurrencyLimiter.run(async () => {
      const { stdout } = await this.streamExecutor.execute('node', [
        lightpandaScript,
        query,
        String(count)
      ], { timeout: CONFIG.TIMEOUT.LIGHTPANDA });
      
      const data = JSON.parse(stdout);
      
      return {
        ...data,
        engine: 'lightpanda'
      };
    });
  }

  // 主搜索逻辑
  async search(query, options = {}) {
    const {
      count = 10,
      engine = 'auto',
      fallback = true
    } = options;
    
    const startTime = Date.now();
    let result;
    let usedEngine;
    
    try {
      // 决定使用哪个引擎
      if (engine === 'lightpanda' || (engine === 'auto' && this.needsBrowser(query))) {
        usedEngine = 'lightpanda';
        console.error(`🔍 [${usedEngine}] ${query}`);
        
        try {
          result = await this.searchLightpanda(query, count);
        } catch (error) {
          if (fallback) {
            console.error(`⚠️ Lightpanda failed, falling back to Tavily...`);
            usedEngine = 'tavily (fallback)';
            result = await this.searchTavily(query, count);
          } else {
            throw error;
          }
        }
      } else {
        usedEngine = 'tavily';
        console.error(`🔍 [${usedEngine}] ${query}`);
        
        try {
          result = await this.searchTavily(query, count);
        } catch (error) {
          if (fallback) {
            console.error(`⚠️ Tavily failed, falling back to Lightpanda...`);
            usedEngine = 'lightpanda (fallback)';
            result = await this.searchLightpanda(query, count);
          } else {
            throw error;
          }
        }
      }
      
      const totalTime = ((Date.now() - startTime) / 1000).toFixed(2);
      const memoryStats = this.memoryMonitor.getStats();
      
      return {
        ...result,
        engine: usedEngine,
        total_time: `${totalTime}s`,
        strategy: engine,
        memory: memoryStats
      };
      
    } finally {
      // 确保资源清理
      await this.resourceCleaner.cleanup();
    }
  }
}

// ============ CLI 入口 ============
async function main() {
  const args = process.argv.slice(2);
  const queryIndex = args.findIndex(arg => !arg.startsWith('--'));
  const query = queryIndex >= 0 ? args[queryIndex] : '';
  
  const options = {
    count: 10,
    engine: 'auto',
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
    console.error('Usage: smart-search-optimized.js <query> [--count N] [--engine auto|tavily|lightpanda] [--no-fallback]');
    process.exit(1);
  }
  
  const searcher = new SmartSearch();
  
  try {
    const result = await searcher.search(query, options);
    console.log(JSON.stringify(result, null, 2));
    process.exit(0);
  } catch (error) {
    console.error(JSON.stringify({
      success: false,
      query,
      error: error.message
    }));
    process.exit(1);
  }
}

main();

