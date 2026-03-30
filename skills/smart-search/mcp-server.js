#!/usr/bin/env node
/**
 * Smart Search MCP Server
 * 提供智能搜索作为 MCP 工具
 */

import { spawn } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));

const smartSearchScript = join(__dirname, '../../scripts/smart-search.js');

// MCP 协议处理
process.stdin.setEncoding('utf8');

let buffer = '';

process.stdin.on('data', (chunk) => {
  buffer += chunk;
  
  let lines = buffer.split('\n');
  buffer = lines.pop(); // 保留不完整的最后一行
  
  for (const line of lines) {
    if (line.trim()) {
      handleRequest(JSON.parse(line));
    }
  }
});

async function handleRequest(request) {
  if (request.method === 'initialize') {
    respond(request.id, {
      protocolVersion: '2024-11-05',
      capabilities: {},
      serverInfo: { name: 'smart-search', version: '1.0.0' }
    });
    return;
  }
  
  if (request.method === 'tools/list') {
    respond(request.id, {
      tools: [{
        name: 'smart_search',
        description: '智能搜索引擎，自动路由到 Tavily 或 Lightpanda',
        inputSchema: {
          type: 'object',
          properties: {
            query: { type: 'string', description: '搜索查询' },
            count: { type: 'number', description: '结果数量', default: 10 },
            engine: { type: 'string', enum: ['auto', 'tavily', 'lightpanda'], default: 'auto' }
          },
          required: ['query']
        }
      }]
    });
    return;
  }
  
  if (request.method === 'tools/call') {
    const { name, arguments: args } = request.params;
    
    if (name === 'smart_search') {
      try {
        const result = await runSmartSearch(args.query, args.count || 10, args.engine || 'auto');
        respond(request.id, {
          content: [{ type: 'text', text: JSON.stringify(result, null, 2) }]
        });
      } catch (error) {
        respond(request.id, {
          content: [{ type: 'text', text: `Error: ${error.message}` }],
          isError: true
        });
      }
    }
    return;
  }
}

function respond(id, result) {
  console.log(JSON.stringify({ jsonrpc: '2.0', id, result }));
}

async function runSmartSearch(query, count, engine) {
  return new Promise((resolve, reject) => {
    const proc = spawn('node', [smartSearchScript, query, '--count', count.toString(), '--engine', engine], {
      cwd: '/root/.openclaw/workspace'
    });
    
    let stdout = '';
    let stderr = '';
    
    proc.stdout.on('data', (data) => stdout += data);
    proc.stderr.on('data', (data) => stderr += data);
    
    proc.on('close', (code) => {
      if (code === 0) {
        try {
          resolve(JSON.parse(stdout));
        } catch {
          resolve({ raw: stdout });
        }
      } else {
        reject(new Error(stderr || `Exit code ${code}`));
      }
    });
  });
}

// 发送初始化通知
console.log(JSON.stringify({ jsonrpc: '2.0', method: 'notifications/initialized' }));
