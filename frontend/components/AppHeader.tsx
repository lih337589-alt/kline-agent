import Link from "next/link";

const navItems = [
  {
    href: "/dashboard",
    label: "Dashboard",
  },
  {
    href: "/stock/AAPL",
    label: "Stock",
  },
  {
    href: "/report/1",
    label: "Report",
  },
  {
    href: "/alerts",
    label: "Alerts",
  },
];

export function AppHeader() {
  return (
    <header className="border-b border-zinc-200 bg-white">
      <div className="mx-auto flex min-h-16 w-full max-w-6xl items-center justify-between px-6">
        <Link
          href="/"
          className="font-semibold tracking-tight text-zinc-950"
        >
          K线之上
        </Link>

        <nav
          aria-label="Primary navigation"
          className="flex items-center gap-5 text-sm text-zinc-600"
        >
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="transition-colors hover:text-zinc-950"
            >
              {item.label}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  );
}
