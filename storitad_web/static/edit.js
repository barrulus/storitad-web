const form = document.getElementById("edit");
form.onsubmit = async (e) => {
  e.preventDefault();
  const id = form.dataset.id;
  const payload = {
    subject: form.subject.value,
    mood: form.mood.value || null,
    tags: form.tags.value.split(",").map(s => s.trim()).filter(Boolean),
    transcript: form.transcript.value,
    notes: form.notes.value,
  };
  const r = await fetch("/api/entries/" + id, {
    method: "PUT", headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (r.ok) location.href = "/entries/" + id; else alert("Save failed: " + r.status);
};
document.getElementById("delete").onclick = async () => {
  if (!confirm("Delete this entry?")) return;
  const r = await fetch("/api/entries/" + form.dataset.id, { method: "DELETE" });
  if (r.ok) location.href = "/entries"; else alert("Delete failed: " + r.status);
};
