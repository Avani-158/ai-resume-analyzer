"use client";

import { motion } from "framer-motion";
import { useAppState } from "@/lib/store";
import {
  BarChart3,
  FileSearch,
  TrendingUp,
  Sparkles,
  BrainCircuit,
  ChevronRight,
} from "lucide-react";
import Link from "next/link";

function StatCard({
  label, value, sub, icon: Icon, color
}: {
  label: string; value: string | number; sub?: string;
  icon: React.ElementType; color: string;
}) {
  return (
    <div className="glass rounded-2xl p-5 flex items-start gap-4">
      <div className={`w-11 h-11 rounded-xl flex items-center justify-center ${color}`}>
        <Icon className="w-5 h-5" />
      </div>
      <div>
        <p className="text-slate-400 text-xs font-medium mb-1">{label}</p>
        <p className="text-2xl font-bold text-white">{value}</p>
        {sub && <p className="text-slate-500 text-xs mt-0.5">{sub}</p>}
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const { state } = useAppState();
  const r = state.results;

  return (
    <div className="p-8 max-w-6xl">
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: -12 }} animate={{ opacity: 1, y: 0 }} className="mb-8">
        <h1 className="text-3xl font-extrabold text-white mb-1">
          Welcome back 👋
        </h1>
        <p className="text-slate-400 text-sm">
          Here&apos;s your career intelligence overview.
        </p>
      </motion.div>

      {r ? (
        <>
          {/* Stats */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            <StatCard label="ATS Score"       value={`${r.ats_score}/100`}       icon={BarChart3}   color="bg-brand-600/20 text-brand-400" />
            <StatCard label="Match Score"     value={`${r.target_match_score}%`} icon={TrendingUp}  color="bg-emerald-600/20 text-emerald-400" sub={state.targetRole} />
            <StatCard label="Skills Found"    value={r.skills.length}            icon={Sparkles}    color="bg-purple-600/20 text-purple-400" />
            <StatCard label="Missing Skills"  value={r.missing_skills.length}    icon={FileSearch}  color="bg-red-600/20 text-red-400" sub="Work on these" />
          </div>

          {/* Top roles preview */}
          <div className="glass rounded-2xl p-6 mb-6">
            <h2 className="font-bold text-white mb-4 flex items-center gap-2">
              <BrainCircuit className="w-5 h-5 text-brand-400" />
              Top Matched Roles
            </h2>
            <div className="space-y-3">
              {r.predicted_roles.slice(0, 3).map((pr) => (
                <div key={pr.role} className="flex items-center gap-3">
                  <div className="flex-1">
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-slate-300 font-medium">{pr.role}</span>
                      <span className="text-brand-400 font-bold">{pr.score}%</span>
                    </div>
                    <div className="progress-bar">
                      <div className="progress-fill" style={{ width: `${Math.min(pr.score, 100)}%` }} />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <Link
            href="/analyzer"
            className="inline-flex items-center gap-2 text-brand-400 hover:text-brand-300 text-sm font-medium transition-colors"
          >
            View Full Analysis <ChevronRight className="w-4 h-4" />
          </Link>
        </>
      ) : (
        /* Empty state */
        <motion.div
          initial={{ opacity: 0, scale: 0.97 }}
          animate={{ opacity: 1, scale: 1 }}
          className="glass rounded-3xl p-12 text-center"
        >
          <div className="w-20 h-20 rounded-2xl bg-brand-600/15 flex items-center justify-center mx-auto mb-6">
            <FileSearch className="w-9 h-9 text-brand-400" />
          </div>
          <h2 className="text-2xl font-bold text-white mb-3">No Analysis Yet</h2>
          <p className="text-slate-400 mb-8 max-w-sm mx-auto">
            Upload your resume to unlock your personalized career dashboard.
          </p>
          <Link
            href="/analyzer"
            id="dashboard-analyze-cta"
            className="inline-flex items-center gap-2 bg-brand-600 hover:bg-brand-500 text-white font-bold px-8 py-3.5 rounded-2xl transition-all hover:shadow-xl hover:shadow-brand-600/30"
          >
            <FileSearch className="w-5 h-5" />
            Analyze My Resume
          </Link>
        </motion.div>
      )}
    </div>
  );
}
