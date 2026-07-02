// storitad_web/static/effects.js
import { ImageSegmenter, FilesetResolver } from "./vendor/mediapipe/tasks-vision.mjs";

const MODEL_URL = "/static/vendor/mediapipe/selfie_segmenter.tflite";
const WASM_ROOT = "/static/vendor/mediapipe/wasm";
const SLOW_MS = 60;         // per-frame budget before we call it "too slow"
const SAMPLE_FRAMES = 30;   // frames to average before deciding
const PERSON_NONZERO = false; // selfie mask: person pixels are zero (verified on device)

let segmenter = null, ready = false;
let kind = "off", bgImage = null;
let rafId = 0, srcVideo = null, outCanvas = null, octx = null;
let work = null, wctx = null, personCanvas = null, pctx = null, maskCanvas = null, mctx = null;
let degradedCb = null, frameTimes = [], decided = false;

function isSupported() {
  const c = document.createElement("canvas");
  return typeof c.captureStream === "function";
}

async function init() {
  if (ready) return true;
  if (!isSupported()) return false;
  try {
    const files = await FilesetResolver.forVisionTasks(WASM_ROOT);
    segmenter = await ImageSegmenter.createFromOptions(files, {
      baseOptions: { modelAssetPath: MODEL_URL },
      runningMode: "VIDEO",
      outputCategoryMask: true,
      outputConfidenceMasks: false,
    });
    ready = true;
    return true;
  } catch (e) {
    console.warn("Effects init failed", e);
    return false;
  }
}

function setEffect(k, opts = {}) {
  kind = k;
  if (k === "image" && opts.imageUrl) {
    const img = new Image();
    img.onload = () => { bgImage = img; };
    img.onerror = () => { bgImage = null; kind = "blur"; };
    img.src = opts.imageUrl;
  } else {
    bgImage = null;
  }
}

function ensureCanvases(w, h) {
  if (!work) { work = document.createElement("canvas"); wctx = work.getContext("2d"); }
  if (!personCanvas) { personCanvas = document.createElement("canvas"); pctx = personCanvas.getContext("2d"); }
  if (!maskCanvas) { maskCanvas = document.createElement("canvas"); mctx = maskCanvas.getContext("2d"); }
  for (const c of [outCanvas, work, personCanvas, maskCanvas]) {
    if (c.width !== w) { c.width = w; c.height = h; }
  }
}

function drawCover(ctx, img, w, h) {
  const r = Math.max(w / img.width, h / img.height);
  const dw = img.width * r, dh = img.height * r;
  ctx.drawImage(img, (w - dw) / 2, (h - dh) / 2, dw, dh);
}

function drawGradient(ctx, w, h) {
  const g = ctx.createLinearGradient(0, 0, w, h);
  g.addColorStop(0, "#F3E4DB"); g.addColorStop(1, "#C45A3B");
  ctx.fillStyle = g; ctx.fillRect(0, 0, w, h);
}

function compositePerson(mask, w, h) {
  const data = mask.getAsUint8Array(); // category index per pixel
  const md = new Uint8ClampedArray(w * h * 4);
  for (let i = 0; i < data.length; i++) {
    const on = (data[i] > 0) === PERSON_NONZERO ? 255 : 0;
    md[i * 4 + 3] = on;
  }
  mctx.putImageData(new ImageData(md, w, h), 0, 0);
  pctx.globalCompositeOperation = "source-over";
  pctx.clearRect(0, 0, w, h);
  pctx.drawImage(srcVideo, 0, 0, w, h);
  pctx.globalCompositeOperation = "destination-in";
  pctx.drawImage(maskCanvas, 0, 0);
  pctx.globalCompositeOperation = "source-over";
  octx.drawImage(personCanvas, 0, 0, w, h);
}

function loop() {
  rafId = requestAnimationFrame(loop);
  if (kind === "off" || !srcVideo) return;
  const w = srcVideo.videoWidth, h = srcVideo.videoHeight;
  if (!w || !h) return;
  ensureCanvases(w, h);
  const t0 = performance.now();
  let result;
  try { result = segmenter.segmentForVideo(srcVideo, t0); }
  catch (e) { return; }
  // background layer
  if (kind === "blur") { wctx.filter = "blur(12px)"; wctx.drawImage(srcVideo, 0, 0, w, h); wctx.filter = "none"; }
  else if (kind === "gradient") { drawGradient(wctx, w, h); }
  else if (kind === "image" && bgImage) { drawCover(wctx, bgImage, w, h); }
  else { wctx.drawImage(srcVideo, 0, 0, w, h); }
  octx.drawImage(work, 0, 0, w, h);
  const mask = result.categoryMask;
  if (mask) { compositePerson(mask, w, h); mask.close(); }
  if (!decided) {
    frameTimes.push(performance.now() - t0);
    if (frameTimes.length >= SAMPLE_FRAMES) {
      decided = true;
      const avg = frameTimes.reduce((a, b) => a + b, 0) / frameTimes.length;
      if (avg > SLOW_MS && degradedCb) degradedCb(avg);
    }
  }
}

function start(sourceVideo, outputCanvas) {
  srcVideo = sourceVideo; outCanvas = outputCanvas; octx = outCanvas.getContext("2d");
  frameTimes = []; decided = false;
  cancelAnimationFrame(rafId);
  loop();
}

function stop() { cancelAnimationFrame(rafId); rafId = 0; srcVideo = null; }

function getOutputStream(fps = 30) {
  return (kind === "off" || !outCanvas) ? null : outCanvas.captureStream(fps);
}

window.Effects = {
  isSupported, init, setEffect, start, stop, getOutputStream,
  onDegraded: (cb) => { degradedCb = cb; },
};
