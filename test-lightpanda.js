import puppeteer from 'puppeteer-core';

const browser = await puppeteer.connect({
  browserWSEndpoint: 'ws://127.0.0.1:9222',
});

const context = await browser.createBrowserContext();
const page = await context.newPage();

console.log('🐼 Testing Lightpanda browser...\n');

// Test 1: Navigate to a simple page
console.log('Test 1: Navigate to example.com');
await page.goto('https://example.com', { waitUntil: 'networkidle0' });
const title = await page.title();
console.log(`  ✓ Page title: "${title}"`);

// Test 2: Extract page content
console.log('Test 2: Extract page content');
const h1 = await page.$eval('h1', el => el.textContent);
const paragraphs = await page.$$eval('p', els => els.map(el => el.textContent));
console.log(`  ✓ H1: "${h1}"`);
console.log(`  ✓ Paragraphs: ${paragraphs.length} found`);

// Test 3: Extract all links
console.log('Test 3: Extract all links');
const links = await page.evaluate(() => {
  return Array.from(document.querySelectorAll('a')).map(a => ({
    text: a.textContent.trim(),
    href: a.getAttribute('href')
  }));
});
console.log(`  ✓ Links found: ${links.length}`);
links.forEach(link => console.log(`    - ${link.text}: ${link.href}`));

// Test 4: JavaScript execution
console.log('Test 4: JavaScript execution');
const jsResult = await page.evaluate(() => {
  return {
    url: window.location.href,
    userAgent: navigator.userAgent,
    timestamp: Date.now()
  };
});
console.log(`  ✓ URL: ${jsResult.url}`);
console.log(`  ✓ User-Agent: ${jsResult.userAgent.slice(0, 50)}...`);

await page.close();
await context.close();
await browser.disconnect();

console.log('\n✅ All tests passed!');
