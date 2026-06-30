let mediaType = "VOICE", stream, recorder, chunks = [], blob, mime, started, stopped;
let previewStream = null, selectedDeviceId = "";

const $ = (id) => document.getElementById(id);

function videoConstraints() {
  return selectedDeviceId
    ? { deviceId: { exact: selectedDeviceId } }
    : { facingMode: "user" };
}

async function listCameras() {
  if (!navigator.mediaDevices?.enumerateDevices) return;
  const cams = (await navigator.mediaDevices.enumerateDevices())
    .filter(d => d.kind === "videoinput");
  const sel = $("camera");
  sel.replaceChildren(...cams.map((c, i) => {
    const o = document.createElement("option");
    o.value = c.deviceId;
    o.textContent = c.label || `Camera ${i + 1}`;
    return o;
  }));
  if (selectedDeviceId) sel.value = selectedDeviceId;
  // Only worth showing when there's an actual choice to make.
  sel.hidden = mediaType !== "VIDEO" || cams.length < 2;
}

function stopPreview() {
  if (previewStream) { previewStream.getTracks().forEach(t => t.stop()); previewStream = null; }
}

async function startPreview() {
  stopPreview();
  try {
    previewStream = await navigator.mediaDevices.getUserMedia({ video: videoConstraints() });
  } catch (err) {
    alert("Camera access is required for video: " + err);
    return;
  }
  selectedDeviceId = previewStream.getVideoTracks()[0]?.getSettings().deviceId || selectedDeviceId;
  $("preview").srcObject = previewStream; $("preview").hidden = false; $("preview").play();
  await listCameras();
}

async function loadRecipients() {
  const list = await (await fetch("/api/recipients")).json();
  const labels = list.map(r => {
    const btn = document.createElement("button");
    btn.type = "button"; btn.className = "chip"; btn.dataset.recipient = r.id;
    btn.textContent = `${r.emoji} ${r.label}`;
    if (r.id === "family") btn.classList.add("active");
    btn.onclick = () => btn.classList.toggle("active");
    return btn;
  });
  $("recipients").replaceChildren(...labels);
  const tags = await (await fetch("/api/recent-tags")).json();
  const chips = tags.map(t => {
    const btn = document.createElement("button");
    btn.type = "button"; btn.className = "chip"; btn.dataset.tag = t; btn.textContent = t;
    return btn;
  });
  $("recent-tags").replaceChildren(...chips);
  $("recent-tags").onclick = (e) => {
    if (!e.target.dataset.tag) return;
    const input = document.querySelector('[name=tags]');
    const set = new Set(input.value.split(",").map(s => s.trim()).filter(Boolean));
    set.add(e.target.dataset.tag);
    input.value = [...set].join(", ");
  };
}

function pickMime() {
  const want = mediaType === "VIDEO"
    ? ["video/mp4", "video/webm;codecs=vp8,opus", "video/webm"]
    : ["audio/mp4", "audio/webm;codecs=opus", "audio/webm"];
  return want.find(t => MediaRecorder.isTypeSupported(t)) || "";
}

async function startRecording() {
  const constraints = mediaType === "VIDEO"
    ? { audio: true, video: videoConstraints() } : { audio: true };
  try {
    stream = await navigator.mediaDevices.getUserMedia(constraints);
  } catch (err) {
    alert("Microphone/camera access is required: " + err);
    $("record").hidden = false; $("stop").hidden = true; $("record").classList.remove("recording");
    return;
  }
  stopPreview();
  if (mediaType === "VIDEO") {
    $("preview").srcObject = stream; $("preview").hidden = false; $("preview").play();
    $("camera").disabled = true;
  }
  mime = pickMime();
  recorder = new MediaRecorder(stream, mime ? { mimeType: mime } : undefined);
  chunks = [];
  recorder.ondataavailable = (e) => e.data.size && chunks.push(e.data);
  recorder.onstop = onStop;
  recorder.start();
  started = Date.now();
  $("record").hidden = true; $("stop").hidden = false;
}

function onStop() {
  stopped = Date.now();
  blob = new Blob(chunks, { type: mime || chunks[0]?.type || "application/octet-stream" });
  stream.getTracks().forEach(t => t.stop());
  $("camera").disabled = false;
  if (mediaType !== "VIDEO") {
    $("playback").src = URL.createObjectURL(blob); $("playback").hidden = false;
  }
  showMeta();
}

async function maybeLocation() {
  if (!$("use-location").checked || !navigator.geolocation) return null;
  return new Promise((res) => navigator.geolocation.getCurrentPosition(
    p => res({ latitude: p.coords.latitude, longitude: p.coords.longitude,
               accuracyMeters: p.coords.accuracy, capturedAt: new Date().toISOString() }),
    () => res(null), { timeout: 5000 }));
}

async function submit(e) {
  e.preventDefault();
  const f = e.target;
  const recipients = [...document.querySelectorAll('#recipients .chip.active')].map(c => c.dataset.recipient);
  const meta = {
    subject: f.subject.value, mediaType, mimeType: blob.type,
    durationSeconds: Math.round((stopped - started) / 1000),
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    recipients, mood: f.mood.value || null,
    tags: f.tags.value.split(",").map(s => s.trim()).filter(Boolean),
    notes: f.notes.value || null, location: await maybeLocation(),
    capturedAt: new Date(started).toISOString(), appVersion: "0.1.0",
  };
  const fd = new FormData();
  fd.append("meta", JSON.stringify(meta));
  fd.append("media", blob, "clip." + (mediaType === "VIDEO" ? "mp4" : "m4a"));
  $("upload").hidden = false;
  const r = await fetch("/api/entries", { method: "POST", body: fd });
  if (r.ok) { const { id } = await r.json(); location.href = "/entries/" + id; }
  else { alert("Upload failed: " + r.status); $("upload").hidden = true; }
}

function tick() {
  if (!started || $("stop").hidden) return;
  const s = Math.floor((Date.now() - started) / 1000);
  $("timer").textContent = Math.floor(s / 60) + ":" + String(s % 60).padStart(2, "0");
}

function showMeta() { $("meta").hidden = false; }

async function probeDuration(file) {
  const url = URL.createObjectURL(file);
  const el = document.createElement(file.type.startsWith("video/") ? "video" : "audio");
  return await new Promise((res) => {
    el.preload = "metadata"; el.src = url;
    el.onloadedmetadata = () => { res(Number.isFinite(el.duration) ? Math.round(el.duration) : 0); URL.revokeObjectURL(url); };
    el.onerror = () => { res(0); URL.revokeObjectURL(url); };
  });
}

async function loadFile(file) {
  stopPreview(); $("camera").hidden = true;
  blob = file;
  mediaType = file.type.startsWith("video/") ? "VIDEO" : "VOICE";
  mime = file.type || "";
  const secs = await probeDuration(file);
  started = file.lastModified || Date.now();
  stopped = started + secs * 1000;
  if (mediaType !== "VIDEO") { $("playback").src = URL.createObjectURL(blob); $("playback").hidden = false; }
  showMeta();
}

$("mode-voice").onclick = () => {
  mediaType = "VOICE"; $("mode-voice").classList.add("active"); $("mode-video").classList.remove("active");
  stopPreview(); $("preview").hidden = true; $("camera").hidden = true;
};
$("mode-video").onclick = () => {
  mediaType = "VIDEO"; $("mode-video").classList.add("active"); $("mode-voice").classList.remove("active");
  $("camera").hidden = false; startPreview();
};
$("camera").onchange = (e) => { selectedDeviceId = e.target.value; if (mediaType === "VIDEO") startPreview(); };
if (navigator.mediaDevices) {
  navigator.mediaDevices.ondevicechange = () => { if (mediaType === "VIDEO") listCameras(); };
}
$("record").onclick = () => { startRecording(); $("record").classList.add("recording"); };
$("stop").onclick = () => { recorder.stop(); $("stop").hidden = true; $("record").hidden = false; $("record").classList.remove("recording"); };
$("pick-file").onclick = () => $("file-input").click();
$("file-input").onchange = (e) => { if (e.target.files[0]) loadFile(e.target.files[0]); };
$("mood-quick").onclick = (e) => {
  const m = e.target.dataset.mood; if (!m) return;
  document.querySelector('[name=mood]').value = m;
};

const h = new Date().getHours();
$("greeting").textContent = h < 12 ? "Good morning" : h < 18 ? "Good afternoon" : "Good evening";

$("meta").onsubmit = submit;
setInterval(tick, 250);
loadRecipients();
