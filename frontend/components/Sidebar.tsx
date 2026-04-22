"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import {
  BrainCircuit,
  LayoutDashboard,
  FileSearch,
  Users,
  MessageSquare,
  Settings,
  ChevronRight,
} from "lucide-react";
import clsx from "clsx";

const navItems = [
  { href: "/dashboard", label: "Dashboard",      icon: LayoutDashboard },
  { href: "/analyzer",  label: "Resume Analyzer", icon: FileSearch },
  { href: "/employer",  label: "Employer Panel",  icon: Users },
  { href: "/chat",      label: "AI Assistant",    icon: MessageSquare },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed left-0 top-0 h-full w-64 bg-surface-card border-r border-surface-border flex flex-col z-40">
      {/* Logo */}
      <div className="h-16 flex items-center gap-2.5 px-6 border-b border-surface-border">
        <div className="w-8 h-8 rounded-lg bg-brand-600/25 flex items-center justify-center">
          <BrainCircuit className="w-5 h-5 text-brand-400" />
        </div>
        <span className="font-extrabold text-lg gradient-text">ResumeAI</span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-6 space-y-1">
        {navItems.map((item, i) => {
          const active = pathname === item.href;
          return (
            <motion.div
              key={item.href}
              initial={{ opacity: 0, x: -16 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.07 }}
            >
              <Link
                href={item.href}
                id={`sidebar-${item.label.toLowerCase().replace(" ", "-")}`}
                className={clsx("sidebar-link", active && "active")}
              >
                <item.icon className="w-4.5 h-4.5 shrink-0" />
                <span className="flex-1">{item.label}</span>
                {active && <ChevronRight className="w-3.5 h-3.5 opacity-60" />}
              </Link>
            </motion.div>
          );
        })}
      </nav>

      {/* Bottom */}
      <div className="px-3 pb-6">
        <Link href="#" className="sidebar-link">
          <Settings className="w-4.5 h-4.5" />
          <span>Settings</span>
        </Link>
        <div className="mt-4 mx-1 p-3 rounded-xl bg-brand-600/10 border border-brand-600/20">
          <p className="text-xs text-brand-300 font-semibold mb-0.5">Pro Tip</p>
          <p className="text-xs text-slate-400">Tailor your resume per job role for higher ATS scores.</p>
        </div>
      </div>
    </aside>
  );
}
