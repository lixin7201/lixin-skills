#!/usr/bin/env node

const { chromium } = require("playwright-core");
const path = require("node:path");

const UID = "1904228041";

async function main() {
  const profileDir = path.resolve(process.argv[2] || "data/weibo-profile");
  const context = await chromium.launchPersistentContext(profileDir, {
    channel: "chrome",
    headless: true,
    viewport: { width: 1280, height: 900 },
  });
  try {
    const page = context.pages()[0] || (await context.newPage());
    await page.goto("https://weibo.com/ceic", {
      waitUntil: "domcontentloaded",
      timeout: 30000,
    });
    const result = await page.evaluate(async (uid) => {
      const response = await fetch(
        `/ajax/statuses/mymblog?uid=${uid}&page=1&feature=0`,
        { credentials: "include", headers: { Accept: "application/json" } },
      );
      if (!response.ok) return { httpStatus: response.status, posts: [] };
      const payload = await response.json();
      const list = payload && payload.data && Array.isArray(payload.data.list)
        ? payload.data.list
        : [];
      const posts = list
        .filter((post) => String(post.user && (post.user.idstr || post.user.id)) === uid)
        .slice(0, 20)
        .map((post) => ({
          idstr: String(post.idstr || post.id || ""),
          created_at: String(post.created_at || ""),
          text_raw: String(post.text_raw || ""),
        }));
      return { httpStatus: response.status, posts };
    }, UID);

    if (result.httpStatus !== 200 || result.posts.length === 0) {
      process.stdout.write(JSON.stringify({ status: "login_required", uid: UID }));
      process.exitCode = 3;
      return;
    }
    process.stdout.write(JSON.stringify({ status: "ok", uid: UID, posts: result.posts }));
  } finally {
    await context.close();
  }
}

main().catch((error) => {
  process.stderr.write(String(error && error.message ? error.message : error));
  process.exit(1);
});
