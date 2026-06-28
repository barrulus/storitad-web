let mediaType = "VOICE", stream, recorder, chunks = [], blob, mime, started;

const $ = (id) => document.getElementById(id);

async function loadRecipients() {
  const list = await (await fetch("/api/recipients")).json();
  $("recipients").innerHTML = "<legend>Recipients</legend>" + list.map(r =>
    `<label><input type="checkbox" name="recipient" value="${r.id}"
      ${r.id === "family" ? "checked" : ""}>${r.emoji} ${r.label}</label>`).join("");
  const tags = await (await fetch("/api/recent-tags")).json();
  $("recent-tags").innerHTML = tags.map(t =>
    `<button type="button" class="chip" data-tag="${t}">${t}</button>`).join("");
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
    ? { audio: true, video: { facingMode: "user" } } : { audio: true };
  stream = await navigator.mediaDevices.getUserMedia(constraints);
  if (mediaType === "VIDEO") {
    $("preview").srcObject = stream; $("preview").hidden = false; $("preview").play();
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
  blob = new Blob(chunks, { type: mime || chunks[0]?.type || "application/octet-stream" });
  stream.getTracks().forEach(t => t.stop());
  if (mediaType !== "VIDEO") {
    $("playback").src = URL.createObjectURL(blob); $("playback").hidden = false;
  }
  $("meta").hidden = false;
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
  const recipients = [...document.querySelectorAll('[name=recipient]:checked')].map(c => c.value);
  const meta = {
    subject: f.subject.value, mediaType, mimeType: blob.type,
    durationSeconds: Math.round((Date.now() - started) / 1000),
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

$("mode-voice").onclick = () => { mediaType = "VOICE"; $("mode-voice").classList.add("active"); $("mode-video").classList.remove("active"); };
$("mode-video").onclick = () => { mediaType = "VIDEO"; $("mode-video").classList.add("active"); $("mode-voice").classList.remove("active"); };
$("record").onclick = startRecording;
$("stop").onclick = () => { recorder.stop(); $("stop").hidden = true; $("record").hidden = false; };
$("meta").onsubmit = submit;
setInterval(tick, 250);
loadRecipients();
