function showPanel(panel) {
  const panels = {
    login: document.getElementById("panel-login"),
    register: document.getElementById("panel-register"),
    reset: document.getElementById("panel-reset")
  };

  // Remove ativo
  for (let p in panels) {
    panels[p].classList.remove("active");
  }

  // Ativa o painel escolhido
  panels[panel].classList.add("active");
}
