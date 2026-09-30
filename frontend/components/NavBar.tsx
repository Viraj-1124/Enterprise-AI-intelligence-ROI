"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/components/AuthProvider";

const MANAGER_LINKS = [
  { href: "/", label: "Dashboard" },
  { href: "/tasks", label: "Tasks" },
  { href: "/employees", label: "Employees" },
  { href: "/departments", label: "Departments" },
  { href: "/prompt-intelligence", label: "Prompt Intelligence" },
  { href: "/agent-optimization", label: "Agent Optimization" },
  { href: "/connectors", label: "Connectors" },
];
const EMPLOYEE_LINKS = [
  { href: "/", label: "My dashboard" },
  { href: "/tasks", label: "My tasks" },
  { href: "/prompt-intelligence", label: "Prompt analyzer" },
  { href: "/agent-optimization", label: "Agent optimizer" },
  { href: "/connectors", label: "Connectors" },
];

export default function NavBar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const links = !user ? [] : user.role === "employee" ? EMPLOYEE_LINKS : MANAGER_LINKS;
  return (
    <header className="sticky top-0 z-30 border-b border-slate-200/80 bg-white/90 backdrop-blur-xl">
      <div className="mx-auto flex max-w-7xl flex-col gap-3 px-5 py-3 sm:px-6 lg:h-[68px] lg:flex-row lg:items-center lg:justify-between lg:gap-8">
        <Link href="/" className="flex w-fit shrink-0 items-center gap-3 rounded-lg outline-none focus-visible:ring-4 focus-visible:ring-indigo-100">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-600 to-violet-700 text-white shadow-sm shadow-indigo-900/20">
            <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" className="h-5 w-5"><path d="m12 2 1.8 6.2L20 10l-6.2 1.8L12 18l-1.8-6.2L4 10l6.2-1.8L12 2Z" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round"/><path d="m19 15 .9 2.1L22 18l-2.1.9L19 21l-.9-2.1L16 18l2.1-.9L19 15Z" fill="currentColor"/></svg>
          </span>
          <span><span className="block text-sm font-semibold tracking-tight text-slate-900">Enterprise AI</span><span className="block text-[10px] font-medium uppercase tracking-[0.14em] text-slate-400">Intelligence platform</span></span>
        </Link>
        <div className="flex min-w-0 items-center gap-3 lg:gap-5">
        <nav aria-label="Main navigation" className="-mx-1 flex min-w-0 items-center gap-1 overflow-x-auto px-1 pb-0.5 text-sm lg:mx-0 lg:gap-1 lg:overflow-visible lg:px-0 lg:pb-0">
          {links.map((l) => {
            const active = l.href === "/" ? pathname === "/" : pathname.startsWith(l.href);
            return <Link key={l.href} href={l.href} aria-current={active ? "page" : undefined} className={`shrink-0 rounded-xl px-3 py-2 text-xs font-medium transition sm:text-sm ${active ? "bg-indigo-50 text-indigo-700" : "text-slate-500 hover:bg-slate-50 hover:text-slate-900"}`}>
              {l.label}
            </Link>;
          })}
        </nav>
        {user && <div className="flex shrink-0 items-center gap-2 border-l border-slate-200 pl-3"><span className="hidden max-w-28 truncate text-xs font-medium text-slate-600 xl:block">{user.name}</span><span className="rounded-lg bg-slate-100 px-2 py-1 text-[10px] font-semibold uppercase tracking-wide text-slate-500">{user.role}</span><button onClick={logout} className="rounded-lg px-2 py-1.5 text-xs font-medium text-slate-500 hover:bg-slate-100 hover:text-slate-800">Sign out</button></div>}
        </div>
      </div>
    </header>
  );
}
