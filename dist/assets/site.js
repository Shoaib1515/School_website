const menuButton = document.querySelector('[data-menu-button]');
const menu = document.querySelector('[data-menu]');
const desktopQuery = matchMedia('(min-width: 1024px)');
const dropdowns = [...document.querySelectorAll('.nav-dropdown')];

function setMenu(open) {
  if (!menu || !menuButton) return;
  menu.classList.toggle('is-open', open);
  menuButton.setAttribute('aria-expanded', String(open));
  document.body.classList.toggle('overflow-hidden', open);
  menuButton.textContent = open ? 'Close' : 'Menu';
  document.querySelector('main')?.toggleAttribute('inert', open);
  document.querySelector('footer')?.toggleAttribute('inert', open);
  if (open) menu.querySelector('a')?.focus();
}

menuButton?.addEventListener('click', () => setMenu(menuButton.getAttribute('aria-expanded') !== 'true'));
menu?.addEventListener('click', event => {
  if (event.target instanceof HTMLAnchorElement) setMenu(false);
});
document.addEventListener('keydown', event => {
  if (event.key === 'Escape') {
    if (menuButton?.getAttribute('aria-expanded') === 'true') {
      setMenu(false);
      menuButton.focus();
    }
    dropdowns.forEach(dropdown => {
      if (dropdown.open) {
        dropdown.open = false;
        dropdown.querySelector('summary').focus();
      }
    });
  }
  if (event.key === 'Tab' && menuButton?.getAttribute('aria-expanded') === 'true') {
    const links = [...menu.querySelectorAll('a')];
    const first = menuButton;
    const last = links.at(-1);
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last?.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  }
});
desktopQuery.addEventListener('change', () => setMenu(false));
dropdowns.forEach(dropdown => {
  dropdown.addEventListener('toggle', () => {
    if (dropdown.open) dropdowns.forEach(other => { if (other !== dropdown) other.open = false; });
  });
  dropdown.addEventListener('focusout', event => {
    if (!dropdown.contains(event.relatedTarget)) dropdown.open = false;
  });
});
document.addEventListener('click', event => {
  dropdowns.forEach(dropdown => { if (!dropdown.contains(event.target)) dropdown.open = false; });
});

document.querySelectorAll('[data-accordion-button]').forEach(button => {
  button.addEventListener('click', () => {
    const panel = document.getElementById(button.getAttribute('aria-controls'));
    const open = button.getAttribute('aria-expanded') === 'true';
    button.setAttribute('aria-expanded', String(!open));
    if (panel) panel.hidden = open;
  });
});

const motionQuery = matchMedia('(prefers-reduced-motion: reduce)');
const reduceMotion = motionQuery.matches;
const reveals = document.querySelectorAll('.reveal');
if (reduceMotion || !('IntersectionObserver' in window)) {
  reveals.forEach(item => item.classList.add('is-visible'));
} else {
  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.remove('is-pending');
        entry.target.classList.add('is-visible');
        observer.unobserve(entry.target);
      }
    });
  }, { rootMargin: '0px 0px -8% 0px', threshold: .08 });
  reveals.forEach(item => {
    if (item.getBoundingClientRect().top > innerHeight) item.classList.add('is-pending');
    observer.observe(item);
  });
  motionQuery.addEventListener('change', event => {
    if (event.matches) {
      observer.disconnect();
      reveals.forEach(item => item.classList.remove('is-pending'));
    }
  });
}

const header = document.querySelector('[data-header]');
const updateHeader = () => header?.classList.toggle('is-scrolled', scrollY > 16);
updateHeader();
addEventListener('scroll', updateHeader, { passive: true });

