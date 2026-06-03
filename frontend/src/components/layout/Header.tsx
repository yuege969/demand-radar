"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_ITEMS = [
  { href: "/", label: "首页" },
  { href: "/categories", label: "行业分类" },
];

export default function Header() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-50 header-mesh border-b border-hairline bg-ground/80 backdrop-blur-xl">
      <div className="mx-auto flex h-12 max-w-7xl items-center justify-between px-4">
        <Link
          href="/"
          className="flex items-center gap-2 text-[15px] font-semibold text-text-primary tracking-tight"
        >
          <svg
            className="h-5 w-5 text-accent"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth={1.5}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M12 3c-4.97 0-9 4.03-9 9s4.03 9 9 9 9-4.03 9-9c0-.46-.04-.92-.1-1.36-.08-.57-.62-.98-1.2-.9-.48.06-.86.44-.86.92v.34A7 7 0 1 1 7 10.5"
            />
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M12 8v5l3 3"
            />
            <circle cx="8" cy="9" r="1.5" fill="currentColor" stroke="none" />
          </svg>
          需求雷达
        </Link>
        <nav className="flex items-center gap-0.5">
          {NAV_ITEMS.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`rounded-md px-3 py-1.5 text-[13px] font-medium transition-colors ${
                pathname === item.href
                  ? "bg-accent-muted text-accent"
                  : "text-text-secondary hover:text-text-primary hover:bg-surface-2"
              }`}
            >
              {item.label}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  );
}
