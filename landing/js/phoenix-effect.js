/**
 * PHOENIX EFFECT
 * ─────────────────────────────────────────────────────────────
 * - Ambient ember particle field (canvas), drifting upward
 * - Hero phoenix (SVG) reacts to scroll: rises, fades, glows
 * - Nav becomes solid on scroll
 * - Proof-strip stat counters animate in when visible
 * All motion respects prefers-reduced-motion.
 * ─────────────────────────────────────────────────────────────
 */

const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

/* ── Ambient ember particles ─────────────────────────────────── */
(function emberField() {
  const canvas = document.getElementById('ember-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  let w, h, particles;

  function resize() {
    w = canvas.width = window.innerWidth;
    h = canvas.height = window.innerHeight;
  }

  function makeParticle() {
    return {
      x: Math.random() * w,
      y: h + Math.random() * 100,
      r: 0.6 + Math.random() * 1.8,
      speed: 0.3 + Math.random() * 0.6,
      drift: (Math.random() - 0.5) * 0.4,
      alpha: 0.2 + Math.random() * 0.5,
      hue: Math.random() > 0.5 ? '242,179,61' : '232,116,43', // gold / flame
    };
  }

  function init() {
    resize();
    const count = Math.min(70, Math.floor((w * h) / 22000));
    particles = Array.from({ length: count }, makeParticle);
  }

  function tick() {
    ctx.clearRect(0, 0, w, h);
    for (const p of particles) {
      p.y -= p.speed;
      p.x += p.drift;
      if (p.y < -20) Object.assign(p, makeParticle(), { y: h + 20 });

      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(${p.hue}, ${p.alpha})`;
      ctx.shadowBlur = 8;
      ctx.shadowColor = `rgba(${p.hue}, ${p.alpha})`;
      ctx.fill();
    }
    if (!reduceMotion) requestAnimationFrame(tick);
  }

  window.addEventListener('resize', init);
  init();
  if (!reduceMotion) requestAnimationFrame(tick);
  else { ctx.clearRect(0, 0, w, h); } // static (empty) canvas if reduced motion
})();

/* ── Scroll-reactive hero phoenix ────────────────────────────── */
(function heroPhoenixScroll() {
  const phoenix = document.getElementById('hero-phoenix');
  const hero = document.getElementById('top');
  if (!phoenix || !hero || reduceMotion) return;

  function update() {
    const heroHeight = hero.offsetHeight;
    const scrollY = window.scrollY;
    const progress = Math.min(1, Math.max(0, scrollY / heroHeight));

    // Rises upward, scales slightly, fades as you scroll past the hero
    const translateY = -progress * 140;
    const scale = 1 + progress * 0.15;
    const opacity = 1 - progress * 1.1;

    phoenix.style.transform = `translate(-50%, calc(-50% + ${translateY}px)) scale(${scale})`;
    phoenix.style.opacity = Math.max(0, opacity);
  }

  window.addEventListener('scroll', update, { passive: true });
  update();
})();

/* ── Nav solid-on-scroll ─────────────────────────────────────── */
(function navScroll() {
  const nav = document.getElementById('nav');
  if (!nav) return;
  function update() {
    nav.classList.toggle('scrolled', window.scrollY > 40);
  }
  window.addEventListener('scroll', update, { passive: true });
  update();
})();

/* ── Proof-strip counters ────────────────────────────────────── */
(function proofCounters() {
  const nums = document.querySelectorAll('.proof-num');
  if (!nums.length) return;

  function animateCount(el) {
    const target = parseInt(el.dataset.target, 10) || 0;
    if (reduceMotion) { el.textContent = target; return; }

    const duration = 1200;
    const start = performance.now();

    function frame(now) {
      const t = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - t, 3);
      el.textContent = Math.floor(eased * target);
      if (t < 1) requestAnimationFrame(frame);
      else el.textContent = target;
    }
    requestAnimationFrame(frame);
  }

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        animateCount(entry.target);
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.4 });

  nums.forEach(n => observer.observe(n));
})();
