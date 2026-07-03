import { useEffect } from 'react';
import { motion, useMotionValue, useSpring, useReducedMotion } from 'framer-motion';

/**
 * A soft brand-green spotlight that trails the cursor.
 * Uses motion values (never React state) so it stays at 60fps and
 * never re-renders the tree. Disabled on touch + reduced-motion.
 */
export function CursorSpotlight() {
  const reduce = useReducedMotion();
  const x = useMotionValue(-400);
  const y = useMotionValue(-400);
  const sx = useSpring(x, { stiffness: 90, damping: 20, mass: 0.6 });
  const sy = useSpring(y, { stiffness: 90, damping: 20, mass: 0.6 });

  useEffect(() => {
    if (reduce) return;
    if (window.matchMedia('(pointer: coarse)').matches) return;
    const move = (e: MouseEvent) => {
      x.set(e.clientX - 300);
      y.set(e.clientY - 300);
    };
    window.addEventListener('mousemove', move);
    return () => window.removeEventListener('mousemove', move);
  }, [reduce, x, y]);

  if (reduce) return null;

  return (
    <motion.div
      aria-hidden
      className="pointer-events-none fixed top-0 left-0 z-[1] hidden md:block h-[600px] w-[600px] rounded-full"
      style={{
        x: sx,
        y: sy,
        background: 'radial-gradient(circle, rgba(27,94,59,0.10) 0%, rgba(244,164,53,0.05) 35%, transparent 65%)',
      }}
    />
  );
}

/**
 * Slow-drifting aurora blobs in brand green + saffron.
 * Position it inside a `relative overflow-hidden` container.
 */
export function AuroraBackdrop({ className = '' }: { className?: string }) {
  return (
    <div aria-hidden className={`absolute inset-0 -z-10 overflow-hidden ${className}`}>
      <div className="aurora-blob aurora-1 w-[42rem] h-[42rem] -top-40 -left-20 bg-primary/20" />
      <div className="aurora-blob aurora-2 w-[34rem] h-[34rem] top-10 right-[-8rem] bg-accent/15" />
      <div className="aurora-blob aurora-3 w-[30rem] h-[30rem] bottom-[-10rem] left-1/3 bg-[#46b96e]/15" />
    </div>
  );
}
