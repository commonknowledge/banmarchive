(() => {
  document.addEventListener('DOMContentLoaded', () => {
    const nav = document.querySelector('.nav');
    document.querySelector('.header__menu-button').addEventListener('click', (ev) => {
      ev.stopPropagation();
      nav.classList.toggle('is-open');
    });
    nav.addEventListener('click', (ev) => {
      ev.stopPropagation();
    });
    document.body.addEventListener('click', () => {
      nav.classList.remove('is-open');
    });
  });
})();
