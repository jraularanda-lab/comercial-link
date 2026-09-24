document.addEventListener('DOMContentLoaded', () => {
  const toggle = document.getElementById('clToggle');
  const sidebar = document.getElementById('clSidebar');
  if (toggle && sidebar) {
    toggle.addEventListener('click', () => sidebar.classList.toggle('open'));
  }
  // Auto-cerrar alertas
  setTimeout(() => {
    document.querySelectorAll('.alert').forEach(a => {
      a.classList.remove('show');
      setTimeout(() => a.remove(), 300);
    });
  }, 4500);
});