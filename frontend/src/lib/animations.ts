import { useEffect, useRef } from 'react';

/**
 * Attaches an IntersectionObserver that adds `.visible` to elements
 * matching `selector` once they enter the viewport.
 */
export function useScrollReveal(selector = '.reveal, .reveal-left, .reveal-right') {
  useEffect(() => {
    const isInViewport = (el: Element) => {
      const rect = el.getBoundingClientRect();
      return rect.top < window.innerHeight && rect.bottom > 0;
    };

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('visible');
            observer.unobserve(entry.target); // fire once
          }
        });
      },
      { threshold: 0.12 }
    );

    const elements = document.querySelectorAll(selector);
    elements.forEach((el) => {
      if (isInViewport(el)) {
        el.classList.add('visible');
        return;
      }
      observer.observe(el);
    });

    return () => observer.disconnect();
  }, [selector]);
}

/**
 * Animates a number counting up from 0 to `target` when the element
 * enters the viewport. Returns a ref to attach to the DOM element.
 */
export function useCountUp(target: number, duration = 1800, suffix = '') {
  const ref = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const animate = () => {
      let start: number | null = null;
      const step = (timestamp: number) => {
        if (!start) start = timestamp;
        const progress = Math.min((timestamp - start) / duration, 1);
        // Ease-out cubic
        const eased = 1 - Math.pow(1 - progress, 3);
        el.textContent = Math.round(eased * target).toLocaleString() + suffix;
        if (progress < 1) requestAnimationFrame(step);
      };
      requestAnimationFrame(step);
    };

    const rect = el.getBoundingClientRect();
    if (rect.top < window.innerHeight && rect.bottom > 0) {
      animate();
      return;
    }

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (!entry.isIntersecting) return;
        observer.disconnect();
        animate();
      },
      { threshold: 0.5 }
    );

    observer.observe(el);
    return () => observer.disconnect();
  }, [target, duration, suffix]);

  return ref;
}
