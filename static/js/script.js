// Shared site behaviour
document.addEventListener("DOMContentLoaded", () => {
  // Confirm before destructive form submits
  document.querySelectorAll("form[data-confirm]").forEach((form) => {
    form.addEventListener("submit", (e) => {
      if (!confirm(form.dataset.confirm)) e.preventDefault();
    });
  });
  // Auto-dismiss flash messages
  document.querySelectorAll(".flash").forEach((el) => {
    setTimeout(() => (el.style.display = "none"), 5000);
  });
});
