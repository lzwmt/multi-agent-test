/**
 * 浏览器 Profile 测试
 * 测试 profile="user" 和 profile="chrome-relay"
 */

async function testUserProfile() {
  console.log("=== 测试: profile='user' (已登录主机浏览器) ===");
  
  try {
    // 尝试使用用户浏览器 profile
    // 注意：需要在有图形界面的 macOS 上运行
    await browser.open({
      url: "https://github.com",
      profile: "user"
    });
    
    await browser.act({ kind: "wait", timeMs: 2000 });
    
    const snapshot = await browser.snapshot();
    console.log("页面标题:", snapshot.title);
    
    // 检查是否已登录（如果有 GitHub 会话）
    const isLoggedIn = snapshot.text?.includes("Sign in") === false;
    console.log("登录状态:", isLoggedIn ? "可能已登录" : "未登录/匿名");
    
    return { success: true, title: snapshot.title, loggedIn: isLoggedIn };
  } catch (e) {
    console.log("user profile 测试需要本地 Chrome:", e.message);
    return { success: false, error: e.message };
  }
}

async function testChromeRelayProfile() {
  console.log("\n=== 测试: profile='chrome-relay' (Chrome 扩展中继) ===");
  
  try {
    // 尝试使用 chrome-relay profile
    // 注意：需要 Chrome 扩展已安装并连接
    await browser.open({
      url: "https://example.com",
      profile: "chrome-relay"
    });
    
    await browser.act({ kind: "wait", timeMs: 2000 });
    
    const snapshot = await browser.snapshot();
    console.log("页面标题:", snapshot.title);
    
    return { success: true, title: snapshot.title };
  } catch (e) {
    console.log("chrome-relay profile 测试需要 Chrome 扩展:", e.message);
    return { success: false, error: e.message };
  }
}

async function testDefaultProfile() {
  console.log("\n=== 测试: 默认 profile (openclaw) ===");
  
  try {
    await browser.open("https://example.com");
    await browser.act({ kind: "wait", timeMs: 1000 });
    
    const snapshot = await browser.snapshot();
    console.log("页面标题:", snapshot.title);
    
    return { success: true, title: snapshot.title };
  } catch (e) {
    console.log("默认 profile 测试失败:", e.message);
    return { success: false, error: e.message };
  }
}

// 主测试流程
async function runProfileTests() {
  console.log("开始浏览器 Profile 测试...\n");
  
  const results = {
    default: await testDefaultProfile(),
    user: await testUserProfile(),
    chromeRelay: await testChromeRelayProfile()
  };
  
  console.log("\n=== Profile 测试结果 ===");
  for (const [name, result] of Object.entries(results)) {
    const status = result.success ? "✅" : "⚠️";
    console.log(`${status} ${name}: ${result.success ? result.title : result.error}`);
  }
  
  return results;
}

module.exports = { runProfileTests };

if (require.main === module) {
  runProfileTests().catch(console.error);
}
