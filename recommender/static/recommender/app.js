// Tab switching between "By title" and "By description", and title autocomplete.
(function () {
  const tabs = document.querySelectorAll(".tab");
  const fields = {
    title: document.querySelector('[data-field="title"]'),
    describe: document.querySelector('[data-field="describe"]'),
  };

  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      const mode = tab.dataset.mode;
      tabs.forEach((t) => {
        t.classList.toggle("active", t === tab);
        t.setAttribute("aria-selected", String(t === tab));
      });
      Object.entries(fields).forEach(([name, el]) => {
        const on = name === mode;
        el.hidden = !on;
        // Disabled inputs are not submitted, so only the active mode is sent.
        el.querySelector("input").disabled = !on;
      });
      fields[mode].querySelector("input").focus();
    });
  });

  const input = document.getElementById("title");
  const list = document.getElementById("title-suggestions");
  let timer;
  input.addEventListener("input", () => {
    clearTimeout(timer);
    const q = input.value.trim();
    if (q.length < 2) return;
    timer = setTimeout(async () => {
      try {
        const res = await fetch(`/api/search?q=${encodeURIComponent(q)}`);
        const data = await res.json();
        list.replaceChildren(
          ...data.titles.map((t) => Object.assign(document.createElement("option"), { value: t }))
        );
      } catch (e) {
        /* autocomplete is optional */
      }
    }, 150);
  });
})();
