#!/usr/bin/env node

const { chromium } = require("playwright-core");
const path = require("node:path");

const UID = "1904228041";

async function main() {
  const profileDir = path.resolve(process.argv[2] || "data/weibo-profile");
  const context = await chromium.launchPersistentContext(profileDir, {
    channel: "chrome",
    headless: false,
    viewport: { width: 1280, height: 900 },
  });
  try {
    const page = context.pages()[0] || (await context.newPage());
    await page.goto("https://weibo.com/ceic", {
      waitUntil: "domcontentloaded",
      timeout: 30000,
    });
    process.stdout.write("请在打开的专用 Chrome 窗口扫码登录微博。\n");
    const deadline = Date.now() + 10 * 60 * 1000;
    while (Date.now() < deadline) {
      const ok = await page.evaluate(async (uid) => {
        try {
          const response = await fetch(
            `/ajax/statuses/mymblog?uid=${uid}&page=1&feature=0`,
            { credentials: "include", headers: { Accept: "application/json" } },
          );
          if (!response.ok) return false;
          const payload = await response.json();
          return Boolean(payload && payload.data && payload.data.list && payload.data.list.length);
        } catch {
          return false;
        }
      }, UID);
      if (ok) {
        process.stdout.write("微博专用登录态已验证。\n");
        return;
      }
      await page.waitForTimeout(3000);
    }
    throw new Error("微博登录等待超时");
  } finally {
    await context.close();
  }
}

main().catch((error) => {
  process.stderr.write(String(error && error.message ? error.message : error));
  process.exit(1);
});
