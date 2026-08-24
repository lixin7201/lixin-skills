#!/usr/bin/env node

const fs = require("node:fs/promises");
const path = require("node:path");

function buildStaticMapRequest(event) {
  if (
    !String(event.location).startsWith("四川宜宾市") ||
    !Number.isFinite(event.latitude) ||
    !Number.isFinite(event.longitude)
  ) {
    throw new Error("invalid earthquake event");
  }

  const center = `${event.longitude.toFixed(6)},${event.latitude.toFixed(6)}`;
  // Baidu Static Map API supports source WGS84 coordinates through coordtype.
  // Source: https://lbsyun.baidu.com/index.php?title=static
  const params = new URLSearchParams({
    ak: "s48fQzziJ0SbX9DcVxW9DToZT2Oo4DAv",
    center,
    width: "690",
    height: "518",
    zoom: "11",
    coordtype: "wgs84ll",
    markers: center,
    markerStyles: "l,M,0xe64545",
  });
  return {
    url: `https://api.map.baidu.com/staticimage/v2?${params}`,
    center,
    params: Object.fromEntries(params),
  };
}

async function main() {
  const [rawEvent, rawOutput] = process.argv.slice(2);
  if (!rawEvent || !rawOutput) {
    throw new Error("usage: screenshot-map.js <event-json> <output.png>");
  }
  const event = JSON.parse(rawEvent);
  const output = path.resolve(rawOutput);
  if (!output.endsWith(".png")) throw new Error("output must be a PNG file");
  const { url, center } = buildStaticMapRequest(event);
  const response = await fetch(url, { signal: AbortSignal.timeout(20000) });
  const bytes = Buffer.from(await response.arrayBuffer());
  if (
    !response.ok ||
    !String(response.headers.get("content-type")).startsWith("image/png") ||
    bytes.length < 10000 ||
    !bytes.subarray(1, 4).equals(Buffer.from("PNG"))
  ) {
    throw new Error("Baidu static map generation failed");
  }
  await fs.mkdir(path.dirname(output), { recursive: true });
  await fs.writeFile(output, bytes);
  process.stdout.write(JSON.stringify({ status: "ok", output, center }));
}

if (require.main === module) {
  main().catch((error) => {
    process.stderr.write(String(error && error.message ? error.message : error));
    process.exit(1);
  });
}

module.exports = { buildStaticMapRequest };
