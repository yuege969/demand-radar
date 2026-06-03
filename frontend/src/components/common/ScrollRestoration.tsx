"use client";

import { useEffect, useRef } from "react";
import { usePathname } from "next/navigation";

const SCROLL_KEY_PREFIX = "scroll-pos:";

export default function ScrollRestoration({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const storageKey = `${SCROLL_KEY_PREFIX}${pathname}`;
  const lastPos = useRef(0);

  // Prevent browser from auto-restoring scroll on back/forward
  useEffect(() => {
    history.scrollRestoration = "manual";
  }, []);

  // Save scroll position during scroll and on unmount
  useEffect(() => {
    let ticking = false;

    const persist = (pos: number) => {
      if (pos > 0) {
        lastPos.current = pos;
        sessionStorage.setItem(storageKey, String(pos));
      }
    };

    const onScroll = () => {
      if (!ticking) {
        requestAnimationFrame(() => {
          persist(window.scrollY);
          ticking = false;
        });
        ticking = true;
      }
    };

    window.addEventListener("scroll", onScroll, { passive: true });

    return () => {
      // Use ref value, not window.scrollY — Next.js may have already
      // scrolled to top during navigation, which would overwrite the
      // real position with 0.
      persist(lastPos.current);
      window.removeEventListener("scroll", onScroll);
    };
  }, [storageKey]);

  // Restore scroll position on mount
  useEffect(() => {
    const saved = sessionStorage.getItem(storageKey);
    if (!saved) return;

    const target = parseInt(saved, 10);
    if (target <= 0) return;

    let attempts = 0;
    const maxAttempts = 20;

    const tryRestore = () => {
      const maxY = document.documentElement.scrollHeight - window.innerHeight;
      if (maxY <= 0) {
        attempts++;
        if (attempts < maxAttempts) {
          requestAnimationFrame(tryRestore);
        }
        return;
      }

      const clamped = Math.min(target, maxY);
      window.scrollTo({ top: clamped, behavior: "instant" as ScrollBehavior });

      // If page hasn't reached target height yet (e.g. async data
      // still loading), retry so the position lands correctly once
      // the full content is rendered.
      if (target > maxY && attempts < maxAttempts) {
        attempts++;
        requestAnimationFrame(tryRestore);
      }
    };

    const timeout = setTimeout(() => tryRestore(), 80);

    return () => clearTimeout(timeout);
  }, [storageKey]);

  return <>{children}</>;
}
