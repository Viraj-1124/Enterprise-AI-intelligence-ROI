import Link from "next/link";

const LINKS = [
  { href: "/", label: "Dashboard" },
  { href: "/tasks", label: "Tasks" },
  { href: "/employees", label: "Employees" },
  { href: "/departments", label: "Departments" },
  { href: "/prompt-intelligence", label: "Prompt Intelligence" },
  { href: "/connectors", label: "Connectors" },
];

export default function NavBar() {
  return (
    <header className="border-b border-gray-200 bg-white">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-3">
        <div className="flex items-center gap-2">
          <div className="h-7 w-7 rounded-md bg-indigo-600" />
          <span className="text-sm font-semibold text-gray-900">Enterprise AI Intelligence</span>
        </div>
        <nav className="flex gap-5 text-sm text-gray-600">
          {LINKS.map((l) => (
            <Link key={l.href} href={l.href} className="hover:text-gray-900">
              {l.label}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  );
}
