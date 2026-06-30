// storitad_web/static/browse.js
const search = document.getElementById("search");
const cards = [...document.querySelectorAll("#entries .entry-card")];
const groups = [...document.querySelectorAll("#entries .date-group")];
search.addEventListener("input", () => {
  const q = search.value.trim().toLowerCase();
  cards.forEach(c => { c.parentElement.hidden = q && !c.dataset.search.includes(q); });
  // hide a date-group header when all its following cards are hidden
  groups.forEach(g => {
    let el = g.nextElementSibling, anyVisible = false;
    while (el && !el.classList.contains("date-group")) {
      if (!el.hidden) anyVisible = true;
      el = el.nextElementSibling;
    }
    g.hidden = !anyVisible;
  });
});
