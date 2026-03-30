#!/usr/bin/env node

/**
 * Lightpanda Search Script
 * 使用 Playwright 通过 CDP 连接 Lightpanda 浏览器进行搜索
 */

const { chromium } = require('playwright');

// 资源跟踪
let resources = { browser: null, context: null, page: null };

// 强制清理函数
async function forceCleanup() {
    if (resources.page) {
        try { await resources.page.close(); } catch {}
    }
    if (resources.context) {
        try { await resources.context.close(); } catch {}
    }
    if (resources.browser) {
        try { await resources.browser.close(); } catch {}
    }
}

// 信号处理
process.on('SIGINT', async () => {
    await forceCleanup();
    process.exit(130);
});
process.on('SIGTERM', async () => {
    await forceCleanup();
    process.exit(143);
});
process.on('uncaughtException', async (err) => {
    console.error('Uncaught:', err.message);
    await forceCleanup();
    process.exit(1);
});

// 解析命令行参数
function parseArgs() {
    const args = process.argv.slice(2);
    const query = args[0] || 'OpenClaw';
    const limit = parseInt(args[1]) || 10;
    return { query, limit };
}

// 主函数
async function main() {
    const { query, limit } = parseArgs();
    const startTime = Date.now();
    const timeout = 30000; // 30秒超时

    let browser = null;
    let context = null;
    let page = null;

    try {
        // 通过 CDP 连接 Lightpanda 浏览器
        resources.browser = await chromium.connectOverCDP('http://localhost:9222');
        browser = resources.browser;

        // 创建新上下文
        resources.context = await browser.newContext({
            viewport: { width: 1920, height: 1080 }
        });
        context = resources.context;

        // 创建新页面
        resources.page = await context.newPage();
        page = resources.page;

        // 设置超时
        page.setDefaultTimeout(timeout);
        page.setDefaultNavigationTimeout(timeout);

        // 访问 Bing 搜索
        const searchUrl = `https://www.bing.com/search?q=${encodeURIComponent(query)}`;
        await page.goto(searchUrl, { waitUntil: 'domcontentloaded' });

        // 等待搜索结果加载
        await page.waitForSelector('#b_results, .b_algo', { timeout: 10000 });

        // 提取搜索结果
        const results = await page.evaluate((maxResults) => {
            const items = [];
            const resultElements = document.querySelectorAll('.b_algo');

            for (let i = 0; i < Math.min(resultElements.length, maxResults); i++) {
                const el = resultElements[i];

                // 提取标题和URL
                const titleLink = el.querySelector('h2 a');
                const title = titleLink ? titleLink.textContent.trim() : '';
                const url = titleLink ? titleLink.href : '';

                // 提取描述
                const descElement = el.querySelector('.b_caption p, .b_snippet p');
                const description = descElement ? descElement.textContent.trim() : '';

                if (title && url) {
                    items.push({ title, url, description });
                }
            }

            return items;
        }, limit);

        // 输出结果
        const output = {
            success: true,
            results: results,
            engine: 'lightpanda',
            query: query,
            count: results.length
        };

        console.log(JSON.stringify(output, null, 2));

    } catch (error) {
        const output = {
            success: false,
            error: error.message,
            engine: 'lightpanda',
            query: query
        };
        console.log(JSON.stringify(output, null, 2));
        process.exit(1);
    } finally {
        // 确保资源被清理
        if (page) {
            try {
                await page.close();
            } catch (e) {
                // 忽略关闭错误
            }
        }
        if (context) {
            try {
                await context.close();
            } catch (e) {
                // 忽略关闭错误
            }
        }
        if (browser) {
            try {
                await browser.close();
            } catch (e) {
                // 忽略关闭错误
            }
        }
    }
}

// 运行主函数
main().catch(error => {
    console.error(JSON.stringify({
        success: false,
        error: error.message,
        engine: 'lightpanda'
    }, null, 2));
    process.exit(1);
});
