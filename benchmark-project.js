import puppeteer from 'puppeteer-core';
import fs from 'fs';

// 中等难度测试项目：电商网站自动化
// 任务：访问电商页面 → 提取商品数据 → 滚动 → 截图

const TEST_URL = 'https://demo-browser.lightpanda.io/campfire-commerce/';
const TEST_DURATION = 30000;

async function runTest(browserType, wsEndpoint) {
  const startTime = Date.now();
  const startMemory = getMemoryInfo();
  
  console.log(`\n🧪 Testing with ${browserType}...`);
  console.log(`   Endpoint: ${wsEndpoint || 'Chrome (local)'}`);
  
  let browser, context, page;
  const results = {
    browserType,
    success: false,
    duration: 0,
    memoryDelta: 0,
    steps: {}
  };
  
  try {
    // 连接浏览器
    const connectStart = Date.now();
    if (wsEndpoint) {
      browser = await puppeteer.connect({ browserWSEndpoint: wsEndpoint });
    } else {
      const chromePath = '/usr/bin/chromium';
      browser = await puppeteer.launch({
        executablePath: chromePath,
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
      });
    }
    results.steps.connect = Date.now() - connectStart;
    
    // 创建上下文和页面
    const setupStart = Date.now();
    context = await browser.createBrowserContext();
    page = await context.newPage();
    await page.setViewport({ width: 1280, height: 720 });
    results.steps.setup = Date.now() - setupStart;
    
    // 导航到测试页面
    const navStart = Date.now();
    await page.goto(TEST_URL, { waitUntil: 'networkidle0', timeout: TEST_DURATION });
    results.steps.navigation = Date.now() - navStart;
    
    // 等待页面加载（使用更通用的选择器）
    const waitStart = Date.now();
    await page.waitForSelector('h1', { timeout: 10000 });
    results.steps.waitForContent = Date.now() - waitStart;
    
    // 提取商品数据
    const extractStart = Date.now();
    const pageData = await page.evaluate(() => {
      // 提取主产品信息
      const mainProduct = {
        name: document.querySelector('h1')?.textContent?.trim() || '',
        price: document.querySelector('h4')?.textContent?.trim() || '',
        description: document.querySelector('p')?.textContent?.trim() || ''
      };
      
      // 提取相关产品
      const relatedProducts = Array.from(document.querySelectorAll('h4')).slice(1).map(h4 => ({
        name: h4.textContent?.trim() || '',
        price: h4.nextElementSibling?.textContent?.trim() || ''
      })).filter(p => p.name && p.price);
      
      // 提取评论
      const reviews = Array.from(document.querySelectorAll('h4')).slice(-3).map(h4 => ({
        title: h4.textContent?.trim()?.substring(0, 50) + '...' || ''
      }));
      
      return {
        title: document.title,
        url: window.location.href,
        userAgent: navigator.userAgent,
        mainProduct,
        relatedProducts,
        reviewCount: reviews.length
      };
    });
    results.steps.extractData = Date.now() - extractStart;
    results.pageData = pageData;
    
    // 模拟滚动
    const scrollStart = Date.now();
    await page.evaluate(() => {
      window.scrollTo(0, document.body.scrollHeight / 2);
    });
    await new Promise(r => setTimeout(r, 300));
    results.steps.scroll = Date.now() - scrollStart;
    
    // 截图
    const screenshotStart = Date.now();
    const screenshotPath = `/tmp/${browserType.toLowerCase().replace(/\s/g, '-')}-screenshot.png`;
    await page.screenshot({ path: screenshotPath, fullPage: false });
    results.steps.screenshot = Date.now() - screenshotStart;
    results.screenshotPath = screenshotPath;
    results.screenshotSize = fs.existsSync(screenshotPath) ? fs.statSync(screenshotPath).size : 0;
    
    // 清理
    await page.close();
    await context.close();
    await browser.disconnect();
    
    results.success = true;
    results.duration = Date.now() - startTime;
    
    // 计算内存变化
    const endMemory = getMemoryInfo();
    results.memoryUsed = startMemory.available - endMemory.available;
    results.memoryPercent = ((results.memoryUsed / startMemory.total) * 100).toFixed(2);
    
  } catch (error) {
    results.error = error.message;
    results.duration = Date.now() - startTime;
    
    try { await page?.close(); } catch {}
    try { await context?.close(); } catch {}
    try { await browser?.disconnect(); } catch {}
  }
  
  return results;
}

function getMemoryInfo() {
  try {
    const memInfo = fs.readFileSync('/proc/meminfo', 'utf8');
    const total = parseInt(memInfo.match(/MemTotal:\s+(\d+)/)?.[1] || 0);
    const available = parseInt(memInfo.match(/MemAvailable:\s+(\d+)/)?.[1] || 0);
    return { total, available };
  } catch {
    return { total: 0, available: 0 };
  }
}

function formatDuration(ms) {
  return `${ms}ms`;
}

function formatBytes(bytes) {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function formatMemoryKB(kb) {
  return `${(kb / 1024).toFixed(1)} MB`;
}

// 主测试流程
async function main() {
  console.log('🚀 E-commerce Automation Benchmark');
  console.log('=====================================');
  console.log(`Target: ${TEST_URL}`);
  console.log('Tasks: Navigate → Wait → Extract → Scroll → Screenshot');
  
  const results = [];
  
  // Test 1: Lightpanda
  const lightpandaResult = await runTest('Lightpanda', 'ws://127.0.0.1:9222');
  results.push(lightpandaResult);
  
  // 等待一下
  await new Promise(r => setTimeout(r, 2000));
  
  // Test 2: Chrome
  let chromeResult;
  try {
    chromeResult = await runTest('Chrome', null);
    results.push(chromeResult);
  } catch (error) {
    console.log('\n⚠️  Chrome test failed:', error.message);
  }
  
  // 输出对比报告
  console.log('\n\n📊 Benchmark Results');
  console.log('====================');
  
  results.forEach(r => {
    console.log(`\n┌─ ${r.browserType} ${'─'.repeat(50)}┐`);
    console.log(`│ Status: ${r.success ? '✅ SUCCESS' : '❌ FAILED'}`);
    if (!r.success) {
      console.log(`│ Error: ${r.error}`);
      console.log(`└${'─'.repeat(60)}┘`);
      return;
    }
    console.log(`│ Total Time: ${formatDuration(r.duration)}`);
    console.log(`│ Memory Used: ${formatMemoryKB(r.memoryUsed)} (${r.memoryPercent}%)`);
    console.log(`│`);
    console.log(`│ Step Breakdown:`);
    Object.entries(r.steps).forEach(([step, time]) => {
      const bar = '█'.repeat(Math.min(Math.floor(time / 50), 20));
      console.log(`│   ${step.padEnd(18)} ${formatDuration(time).padStart(6)} ${bar}`);
    });
    console.log(`│`);
    console.log(`│ Data Extracted:`);
    console.log(`│   Title: ${r.pageData?.title || 'N/A'}`);
    console.log(`│   Main Product: ${r.pageData?.mainProduct?.name || 'N/A'}`);
    console.log(`│   Price: ${r.pageData?.mainProduct?.price || 'N/A'}`);
    console.log(`│   Related Products: ${r.pageData?.relatedProducts?.length || 0}`);
    console.log(`│   Reviews: ${r.pageData?.reviewCount || 0}`);
    console.log(`│`);
    console.log(`│ Screenshot: ${formatBytes(r.screenshotSize)}`);
    console.log(`│ User-Agent: ${r.pageData?.userAgent?.slice(0, 40) || 'N/A'}...`);
    console.log(`└${'─'.repeat(60)}┘`);
  });
  
  // 对比总结
  if (results.length === 2 && results.every(r => r.success)) {
    const [lightpanda, chrome] = results;
    const speedDiff = ((chrome.duration - lightpanda.duration) / chrome.duration * 100).toFixed(1);
    const memoryDiff = ((chrome.memoryUsed - lightpanda.memoryUsed) / chrome.memoryUsed * 100).toFixed(1);
    
    console.log('\n\n🔍 Comparison Summary');
    console.log('====================');
    console.log(`\n⚡ Speed:`);
    console.log(`   Lightpanda: ${formatDuration(lightpanda.duration)}`);
    console.log(`   Chrome:     ${formatDuration(chrome.duration)}`);
    console.log(`   Winner: ${lightpanda.duration < chrome.duration ? '🐼 Lightpanda' : '🔵 Chrome'} (${Math.abs(speedDiff)}% ${lightpanda.duration < chrome.duration ? 'faster' : 'slower'})`);
    
    console.log(`\n💾 Memory:`);
    console.log(`   Lightpanda: ${formatMemoryKB(lightpanda.memoryUsed)}`);
    console.log(`   Chrome:     ${formatMemoryKB(chrome.memoryUsed)}`);
    console.log(`   Winner: ${lightpanda.memoryUsed < chrome.memoryUsed ? '🐼 Lightpanda' : '🔵 Chrome'} (${Math.abs(memoryDiff)}% ${lightpanda.memoryUsed < chrome.memoryUsed ? 'less' : 'more'})`);
    
    console.log(`\n📋 Implementation Completeness:`);
    console.log(`   Lightpanda: ${lightpanda.pageData?.mainProduct?.name ? '✅ Full' : '⚠️ Partial'}`);
    console.log(`   Chrome:     ${chrome.pageData?.mainProduct?.name ? '✅ Full' : '⚠️ Partial'}`);
    console.log(`\n🏆 Overall Winner: ${lightpanda.duration < chrome.duration && lightpanda.memoryUsed < chrome.memoryUsed ? '🐼 Lightpanda' : '🔵 Chrome'}`);
  }
}

main().catch(console.error);