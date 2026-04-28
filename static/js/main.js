/* ЗАО ПП «УРАЛ» — Main JavaScript */
document.addEventListener('DOMContentLoaded', function () {

  /* ── Hero Slider ─────────────────────────────────────── */
  const slides = document.querySelectorAll('.slide');
  const dots   = document.querySelectorAll('.slider-dot');
  let current  = 0;
  let timer;

  function showSlide(n) {
    slides.forEach(s => s.classList.remove('active'));
    dots.forEach(d => d.classList.remove('active'));
    current = (n + slides.length) % slides.length;
    if (slides[current]) slides[current].classList.add('active');
    if (dots[current])   dots[current].classList.add('active');
  }

  function nextSlide() { showSlide(current + 1); }
  function prevSlide() { showSlide(current - 1); }
  function autoPlay()  { timer = setInterval(nextSlide, 5000); }
  function stopPlay()  { clearInterval(timer); }

  const prevBtn = document.querySelector('.slider-arrow.prev');
  const nextBtn = document.querySelector('.slider-arrow.next');
  if (prevBtn) prevBtn.addEventListener('click', () => { stopPlay(); prevSlide(); autoPlay(); });
  if (nextBtn) nextBtn.addEventListener('click', () => { stopPlay(); nextSlide(); autoPlay(); });
  dots.forEach((dot, i) => dot.addEventListener('click', () => { stopPlay(); showSlide(i); autoPlay(); }));

  if (slides.length) { showSlide(0); autoPlay(); }

  /* ── Mobile Menu ─────────────────────────────────────── */
  const toggle  = document.querySelector('.menu-toggle');
  const navList = document.querySelector('.nav-list');
  if (toggle && navList) {
    toggle.addEventListener('click', () => {
      navList.classList.toggle('open');
      toggle.classList.toggle('open');
    });
  }

  /* ── Dropdown on mobile ──────────────────────────────── */
  if (window.innerWidth <= 768) {
    document.querySelectorAll('.nav-link').forEach(link => {
      link.addEventListener('click', function (e) {
        const dropdown = this.nextElementSibling;
        if (dropdown && dropdown.classList.contains('dropdown')) {
          e.preventDefault();
          const visible = dropdown.style.display === 'block';
          document.querySelectorAll('.dropdown').forEach(d => d.style.display = 'none');
          dropdown.style.display = visible ? 'none' : 'block';
        }
      });
    });
  }

  /* ── FAQ Accordion ───────────────────────────────────── */
  document.querySelectorAll('.faq-question').forEach(q => {
    q.addEventListener('click', function () {
      const item   = this.closest('.faq-item');
      const answer = item.querySelector('.faq-answer');
      const isOpen = item.classList.contains('open');
      // Close all
      document.querySelectorAll('.faq-item').forEach(fi => {
        fi.classList.remove('open');
        fi.querySelector('.faq-answer').style.maxHeight = '0';
      });
      if (!isOpen) {
        item.classList.add('open');
        answer.style.maxHeight = answer.scrollHeight + 'px';
      }
    });
  });

  /* ── Scroll Reveal ───────────────────────────────────── */
  const revealEls = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12 });
    revealEls.forEach(el => observer.observe(el));
  } else {
    revealEls.forEach(el => el.classList.add('visible'));
  }

  /* ── Sticky header shadow ────────────────────────────── */
  const headerMain = document.querySelector('.header-main');
  if (headerMain) {
    window.addEventListener('scroll', () => {
      headerMain.style.boxShadow = window.scrollY > 10
        ? '0 4px 20px rgba(0,0,0,0.15)'
        : '0 2px 16px rgba(0,0,0,0.08)';
    });
  }

  /* ── Highlight active nav item ───────────────────────── */
  const path = window.location.pathname;
  document.querySelectorAll('.nav-link').forEach(link => {
    const href = link.getAttribute('href');
    if (href && href !== '/' && path.startsWith(href)) {
      link.classList.add('active');
    } else if (href === '/' && path === '/') {
      link.classList.add('active');
    }
  });
});
