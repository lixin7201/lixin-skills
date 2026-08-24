#!/usr/bin/env node

const { spawn } = require("node:child_process");
const path = require("node:path");

const PROJECT_ROOT = path.resolve(__dirname, "..");
const PYTHON = process.env.EARTHQUAKE_PATROL_PYTHON || "python3";
const PUBLISH_ENABLED = process.env.WOLFX_PUBLISH_ENABLED === "1";
const ENDPOINTS = [
  {
    channel: "sc_eew",
    url: "wss://ws-api.wolfx.jp/sc_eew",
    query: "query_sceew",
  },
  {
    channel: "cenc_eew",
    url: "wss://ws-api.wolfx.jp/cenc_eew",
    query: "query_cenceew",
  },
];

function backoffSeconds(attempt) {
  return Math.min(30, 2 ** Math.max(0, Number(attempt) || 0));
}

function log(payload) {
  process.stdout.write(`${JSON.stringify({
    at: new Date().toISOString(),
    ...payload,
  })}\n`);
}

function handoff(payload, channel, attempt = 0) {
  return new Promise((resolve) => {
    const args = [path.join(PROJECT_ROOT, "earthquake_patrol.py"), "wolfx-event"];
    if (PUBLISH_ENABLED) args.push("--publish");
    const child = spawn(PYTHON, args, {
      cwd: PROJECT_ROOT,
      stdio: ["pipe", "pipe", "pipe"],
      env: process.env,
    });
    let stdout = "";
    let stderr = "";
    child.stdout.setEncoding("utf8");
    child.stderr.setEncoding("utf8");
    child.stdout.on("data", (chunk) => { stdout += chunk; });
    child.stderr.on("data", (chunk) => { stderr += chunk; });
    child.on("close", (code) => {
      if ((code === 75 || code === 76) && attempt < 12) {
        log({
          event: "handoff_retry",
          channel,
          attempt: attempt + 1,
          retryInSeconds: 5,
        });
        setTimeout(
          () => resolve(handoff(payload, channel, attempt + 1)),
          5000,
        );
        return;
      }
      log({
        event: "handoff_complete",
        channel,
        mode: PUBLISH_ENABLED ? "publish" : "shadow",
        exitCode: code,
        result: stdout.trim().slice(0, 4000),
        error: stderr.trim().slice(0, 1000),
      });
      resolve(code);
    });
    child.on("error", (error) => {
      log({ event: "handoff_error", channel, error: String(error.message || error) });
      resolve(1);
    });
    child.stdin.end(JSON.stringify({ ...payload, _wolfx_channel: channel }));
  });
}

function connect(endpoint) {
  let stopped = false;
  let reconnectAttempt = 0;
  let socket = null;
  let reconnectTimer = null;

  const scheduleReconnect = (details = {}) => {
    if (stopped || reconnectTimer) return;
    const delay = backoffSeconds(reconnectAttempt++);
    log({
      event: "disconnected",
      channel: endpoint.channel,
      retryInSeconds: delay,
      ...details,
    });
    reconnectTimer = setTimeout(() => {
      reconnectTimer = null;
      open();
    }, delay * 1000);
  };

  const open = () => {
    if (stopped) return;
    const currentSocket = new WebSocket(endpoint.url);
    socket = currentSocket;
    let socketFailed = false;
    currentSocket.addEventListener("open", () => {
      reconnectAttempt = 0;
      log({ event: "connected", channel: endpoint.channel, url: endpoint.url });
      currentSocket.send(endpoint.query);
    });
    currentSocket.addEventListener("message", async (message) => {
      let payload;
      try {
        payload = JSON.parse(String(message.data));
      } catch (error) {
        log({ event: "invalid_json", channel: endpoint.channel });
        return;
      }
      if (payload && payload.type === "heartbeat") {
        if (currentSocket.readyState === WebSocket.OPEN) currentSocket.send("ping");
        log({ event: "heartbeat", channel: endpoint.channel });
        return;
      }
      if (payload && payload.type === "pong") return;
      await handoff(payload, endpoint.channel);
    });
    currentSocket.addEventListener("error", () => {
      if (socketFailed) return;
      socketFailed = true;
      log({ event: "socket_error", channel: endpoint.channel });
      scheduleReconnect({ reason: "socket_error" });
    });
    currentSocket.addEventListener("close", (message) => {
      scheduleReconnect({ code: message.code });
    });
  };

  open();
  return () => {
    stopped = true;
    if (reconnectTimer) clearTimeout(reconnectTimer);
    if (socket) socket.close(1000, "shutdown");
  };
}

function main() {
  if (process.argv.includes("--self-test")) {
    process.stdout.write(JSON.stringify({
      status: "ok",
      publishEnabled: PUBLISH_ENABLED,
      endpoints: ENDPOINTS,
      backoffSeconds: [backoffSeconds(0), backoffSeconds(1), backoffSeconds(9)],
    }));
    return;
  }
  const stops = ENDPOINTS.map(connect);
  const shutdown = () => {
    for (const stop of stops) stop();
  };
  process.once("SIGINT", shutdown);
  process.once("SIGTERM", shutdown);
}

if (require.main === module) main();

module.exports = { ENDPOINTS, backoffSeconds, handoff };
