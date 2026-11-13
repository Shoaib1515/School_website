(() => {
  const motion = window.Motion;
  const preference = matchMedia('(prefers-reduced-motion: reduce)');
  const running = new Set();
  function animate(element, frames, options = {}) {
    if (!motion || preference.matches || !element) return;
    const control = motion.animate(element, frames, { duration: .45, ease: [.22, 1, .36, 1], ...options });
    running.add(control);
    Promise.resolve(control).finally(() => running.delete(control));
    return control;
  }
  if (motion && !preference.matches) {
    document.documentElement.classList.add('motion-ready');
    animate('.hero-copy > *', { opacity: [0, 1], y: [22, 0] }, { delay: motion.stagger(.065), duration: .55 });
    animate('.hero-photo > img', { scale: [1.045, 1] }, { duration: .9 });
    motion.inView('.stage-explorer, .news-grid, .related-grid', element => {
      const children = element.querySelectorAll('.news-tile, .related-grid > a, [role="tab"]');
      if (children.length) animate(children, { opacity: [0, 1], y: [20, 0] }, { delay: motion.stagger(.065) });
    });
  }
  const progress = document.querySelector('.reading-progress');
  let stopProgress;
  if (motion && !preference.matches) {
    stopProgress = motion.scroll(motion.animate(progress, { scaleX: [0, 1] }, { ease: 'linear' }));
  }
  preference.addEventListener('change', event => {
    if (!event.matches) return;
    running.forEach(control => control.complete());
    stopProgress?.();
    progress.style.transform = 'none';
    document.documentElement.classList.remove('motion-ready');
  });

  document.querySelectorAll('[data-photo-src]').forEach(button => {
    button.addEventListener('click', () => {
      const figure = button.closest('.hero-photo');
      const image = figure.querySelector('img');
      if (!image || button.getAttribute('aria-pressed') === 'true') return;
      image.src = button.dataset.photoSrc;
      image.alt = button.dataset.photoAlt;
      figure.querySelectorAll('[data-photo-src]').forEach(item => item.setAttribute('aria-pressed', String(item === button)));
      animate(image, { opacity: [.6, 1], scale: [1.025, 1] }, { duration: .35 });
    });
  });

  document.querySelectorAll('[data-tabs]').forEach(explorer => {
    const tabs = [...explorer.querySelectorAll('[role="tab"]')];
    function activate(tab, focus = false) {
      tabs.forEach(item => {
        const selected = item === tab;
        item.setAttribute('aria-selected', String(selected));
        item.tabIndex = selected ? 0 : -1;
        const panel = document.getElementById(item.getAttribute('aria-controls'));
        panel.hidden = !selected;
        if (selected) animate(panel, { opacity: [.5, 1], y: [10, 0] }, { duration: .3 });
      });
      if (focus) tab.focus();
    }
    tabs.forEach((tab, index) => {
      tab.addEventListener('click', () => activate(tab));
      tab.addEventListener('keydown', event => {
        let next;
        if (event.key === 'ArrowRight') next = (index + 1) % tabs.length;
        if (event.key === 'ArrowLeft') next = (index - 1 + tabs.length) % tabs.length;
        if (event.key === 'Home') next = 0;
        if (event.key === 'End') next = tabs.length - 1;
        if (next !== undefined) { event.preventDefault(); activate(tabs[next], true); }
      });
    });
  });
  document.querySelectorAll('.read-more, .journey-step').forEach(details => {
    details.addEventListener('toggle', () => {
      if (!details.open) return;
      if (details.classList.contains('journey-step')) {
        details.parentElement.querySelectorAll('.journey-step').forEach(other => { if (other !== details) other.open = false; });
      }
      const content = details.querySelector(':scope > div');
      animate(content, { opacity: [0, 1], y: [8, 0] }, { duration: .25 });
    });
  });

  const dialog = document.getElementById('site-search');
  const query = document.getElementById('page-search');
  const results = [...dialog.querySelectorAll('[data-search-result]')];
  const status = dialog.querySelector('[data-search-status]');
  const launch = document.querySelector('[data-search-open]');
  const openSearch = () => {
    if (dialog.open) return;
    dialog.showModal();
    query.focus();
    animate(dialog, { opacity: [0, 1], y: [14, 0], scale: [.98, 1] }, { duration: .25 });
  };
  launch.addEventListener('click', openSearch);
  dialog.querySelector('[data-search-close]').addEventListener('click', () => dialog.close());
  dialog.addEventListener('keydown', event => {
    if (event.key === 'Escape') {
      event.preventDefault();
      dialog.close();
    }
  });
  dialog.addEventListener('click', event => { if (event.target === dialog) { const rect = dialog.getBoundingClientRect(); if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) dialog.close(); } });
  dialog.addEventListener('close', () => launch.focus());
  query.addEventListener('input', () => {
    const term = query.value.toLowerCase().trim();
    let count = 0;
    results.forEach(link => { link.hidden = !link.textContent.toLowerCase().includes(term); if (!link.hidden) count++; });
    status.textContent = count ? `${count} school ${count === 1 ? 'page' : 'pages'}` : 'No pages found. Try admissions, campus or calendar.';
  });
  document.addEventListener('keydown', event => {
    if (event.key === '/' && !event.ctrlKey && !event.metaKey && !event.altKey && !['INPUT','TEXTAREA','SELECT'].includes(document.activeElement.tagName) && !document.activeElement.isContentEditable) {
      event.preventDefault(); openSearch();
    }
  });
  const backTop = document.querySelector('.back-top');
  const updateTop = () => { backTop.hidden = scrollY < 600; };
  updateTop();
  addEventListener('scroll', updateTop, { passive: true });
})();
