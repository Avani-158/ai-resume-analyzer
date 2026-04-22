"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useAppState } from "@/lib/store";
import { analyzeResume, fetchRoles } from "@/lib/api";
import toast from "react-hot-toast";
import {
  UploadCloud,
  FileText,
  X,
  Loader2,
  BrainCircuit,
  BarChart3,
  Sparkles,
  BookOpen,
  CheckCircle2,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  Target,
  Lightbulb,
} from "lucide-react";

// ── Sub-components ───────────────────────────────────────────────────────────

function ScoreRing({ score, label }: { score: number; label: string }) {
  const r = 44;
  const circ = 2 * Math.PI * r;
  const dash = circ * (score / 100);

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative w-28 h-28">
        <svg className="w-28 h-28 -rotate-90" viewBox="0 0 100 100">
          <circle cx="50" cy="50" r={r} fill="none" stroke="#1e1e3a" strokeWidth="10" />
          <motion.circle
            cx="50" cy="50" r={r}
            fill="none"
            stroke="url(#scoreGrad)"
            strokeWidth="10"
            strokeLinecap="round"
            strokeDasharray={circ}
            initial={{ strokeDashoffset: circ }}
            animate={{ strokeDashoffset: circ - dash }}
            transition={{ duration: 1.4, ease: "easeOut" }}
          />
          <defs>
            <linearGradient id="scoreGrad" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stopColor="#6366f1" />
              <stop offset="100%" stopColor="#8b5cf6" />
            </linearGradient>
          </defs>
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-2xl font-extrabold text-white">{score}</span>
        </div>
      </div>
      <span className="text-xs text-slate-400 font-medium">{label}</span>
    </div>
  );
}

function ProgressBar({ score, label }: { score: number; label: string }) {
  return (
    <div className="mb-3">
      <div className="flex justify-between text-sm mb-1.5">
        <span className="text-slate-300 font-medium">{label}</span>
        <span className="text-brand-400 font-bold">{score}%</span>
      </div>
      <div className="progress-bar">
        <motion.div
          className="progress-fill"
          initial={{ width: 0 }}
          animate={{ width: `${Math.min(score, 100)}%` }}
          transition={{ duration: 1.2, ease: "easeOut" }}
        />
      </div>
    </div>
  );
}

function SectionCard({ title, icon: Icon, children }: {
  title: string; icon: React.ElementType; children: React.ReactNode;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass rounded-2xl p-6"
    >
      <h3 className="font-bold text-white flex items-center gap-2 mb-4">
        <Icon className="w-5 h-5 text-brand-400" />
        {title}
      </h3>
      {children}
    </motion.div>
  );
}

// ── Main Page ────────────────────────────────────────────────────────────────

const FALLBACK_ROLES = [
  "AI Engineer",
  "Backend Developer",
  "Computer Vision Engineer",
  "Data Analyst",
  "Data Scientist",
  "DevOps Engineer",
  "Frontend Developer",
  "Full Stack Developer",
  "Machine Learning",
  "ML Engineer",
  "NLP Engineer",
  "Software Engineer",
];

export default function AnalyzerPage() {
  const { state, dispatch } = useAppState();
  const [dragging, setDragging] = useState(false);
  const [showAllRoles, setShowAllRoles] = useState(false);
  const [roles, setRoles] = useState<string[]>(FALLBACK_ROLES);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    let mounted = true;
    fetchRoles()
      .then((fetched) => {
        if (mounted && fetched.length > 0) {
          setRoles(fetched);
        }
      })
      .catch(() => {
        // Keep fallback roles when backend role fetch fails.
      });
    return () => {
      mounted = false;
    };
  }, []);

  const handleFile = (file: File) => {
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      toast.error("Please upload a PDF file");
      return;
    }
    dispatch({ type: "SET_FILE", payload: file });
  };

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  }, []);

  const handleAnalyze = async () => {
    if (!state.uploadedFile) return toast.error("Please upload a PDF resume");
    if (!state.targetRole)   return toast.error("Please enter a target role");

    dispatch({ type: "SET_LOADING", payload: true });
    dispatch({ type: "SET_ERROR",   payload: null });

    try {
      const result = await analyzeResume(state.uploadedFile, state.targetRole);
      dispatch({ type: "SET_RESULTS", payload: result });
      toast.success("Analysis complete! 🎉");
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Analysis failed";
      dispatch({ type: "SET_ERROR", payload: message });
      toast.error(message);
    }
  };

  const r = state.results;

  return (
    <div className="p-8 max-w-6xl">
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: -12 }} animate={{ opacity: 1, y: 0 }} className="mb-8">
        <h1 className="text-3xl font-extrabold text-white mb-1 flex items-center gap-3">
          <BrainCircuit className="w-8 h-8 text-brand-400" />
          Resume Analyzer
        </h1>
        <p className="text-slate-400 text-sm">
          Upload your PDF resume and set a target role to get your full AI analysis.
        </p>
      </motion.div>

      {/* Upload Card */}
      <div className="glass rounded-2xl p-6 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Drop Zone */}
          <div
            onDragOver={e => { e.preventDefault(); setDragging(true); }}
            onDragLeave={() => setDragging(false)}
            onDrop={onDrop}
            onClick={() => fileRef.current?.click()}
            className={`relative border-2 border-dashed rounded-2xl p-8 flex flex-col items-center justify-center gap-3 cursor-pointer transition-all duration-200 ${
              dragging
                ? "border-brand-500 bg-brand-600/10"
                : "border-surface-border hover:border-brand-500/50 hover:bg-surface-hover"
            }`}
          >
            <input
              ref={fileRef}
              type="file"
              accept=".pdf"
              id="resume-file-input"
              className="hidden"
              onChange={e => e.target.files?.[0] && handleFile(e.target.files[0])}
            />
            {state.uploadedFile ? (
              <>
                <div className="w-14 h-14 rounded-xl bg-brand-600/20 flex items-center justify-center">
                  <FileText className="w-7 h-7 text-brand-400" />
                </div>
                <p className="text-white font-semibold text-center text-sm">{state.uploadedFile.name}</p>
                <button
                  onClick={e => { e.stopPropagation(); dispatch({ type: "SET_FILE", payload: null }); }}
                  className="absolute top-3 right-3 p-1.5 rounded-lg hover:bg-surface-border text-slate-400 hover:text-white transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              </>
            ) : (
              <>
                <UploadCloud className={`w-10 h-10 ${dragging ? "text-brand-400" : "text-slate-500"}`} />
                <p className="text-slate-400 text-sm text-center">
                  <span className="text-brand-400 font-semibold">Click to upload</span> or drag & drop
                </p>
                <p className="text-slate-500 text-xs">PDF only · Max 10 MB</p>
              </>
            )}
          </div>

            {/* Role Input */}
          <div className="flex flex-col gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                Target Role
              </label>
              <input
                id="target-role-input"
                type="text"
                  list="role-options"
                value={state.targetRole}
                onChange={e => dispatch({ type: "SET_ROLE", payload: e.target.value })}
                  placeholder="Search and select a role"
                className="w-full bg-surface-border/40 border border-surface-border rounded-xl px-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:border-brand-500 transition-colors text-sm"
              />
                <datalist id="role-options">
                  {roles.map(role => (
                    <option key={role} value={role} />
                  ))}
                </datalist>
                <p className="text-xs text-slate-500 mt-2">
                  Start typing to search roles from the dropdown.
                </p>
            </div>
            {/* Quick role pills */}
            <div>
              <p className="text-xs text-slate-500 mb-2">Quick select:</p>
              <div className="flex flex-wrap gap-2">
                {roles.slice(0, 5).map(role => (
                  <button
                    key={role}
                    id={`role-pill-${role.toLowerCase().replace(/ /g, "-")}`}
                    onClick={() => dispatch({ type: "SET_ROLE", payload: role })}
                    className={`text-xs px-3 py-1.5 rounded-full border transition-all ${
                      state.targetRole === role
                        ? "bg-brand-600/30 border-brand-500/50 text-brand-300"
                        : "border-surface-border text-slate-400 hover:border-brand-500/40 hover:text-slate-300"
                    }`}
                  >
                    {role}
                  </button>
                ))}
              </div>
            </div>

            <button
              id="analyze-btn"
              onClick={handleAnalyze}
              disabled={state.loading}
              className="mt-auto flex items-center justify-center gap-2 bg-brand-600 hover:bg-brand-500 disabled:opacity-60 disabled:cursor-not-allowed text-white font-bold py-3.5 rounded-xl transition-all hover:shadow-xl hover:shadow-brand-600/30"
            >
              {state.loading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Analyzing…
                </>
              ) : (
                <>
                  <Sparkles className="w-5 h-5" />
                  Analyze Resume
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Error */}
      <AnimatePresence>
        {state.error && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="flex items-center gap-3 bg-red-900/20 border border-red-500/30 rounded-xl px-5 py-4 mb-6 text-red-300 text-sm"
          >
            <AlertTriangle className="w-5 h-5 shrink-0" />
            {state.error}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Loading skeleton */}
      {state.loading && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="glass rounded-2xl p-6 h-48 shimmer" />
          ))}
        </div>
      )}

      {/* ── Results ─────────────────────────────────────────── */}
      {r && !state.loading && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="space-y-6"
        >
          {/* Score Overview */}
          <SectionCard title="Score Overview" icon={BarChart3}>
            <div className="flex flex-wrap gap-8 items-center justify-around">
              <ScoreRing score={Math.round(r.ats_score)}          label="ATS Score" />
              <ScoreRing score={Math.round(r.target_match_score)} label="Match Score" />
              <div className="flex-1 min-w-48">
                <ProgressBar score={r.target_match_score} label={`${state.targetRole || "Target Role"} Match`} />
                <ProgressBar score={r.skills.length * 4}  label="Skill Coverage" />
              </div>
            </div>
          </SectionCard>

          {/* Top 3 Roles */}
          <SectionCard title="Predicted Roles" icon={Target}>
            <div className="space-y-3">
              {(showAllRoles ? r.predicted_roles : r.predicted_roles.slice(0, 3)).map((pr, i) => (
                <motion.div
                  key={pr.role}
                  initial={{ opacity: 0, x: -12 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.07 }}
                >
                  <div className="flex justify-between text-sm mb-1.5">
                    <span className="text-slate-300 font-medium">
                      {i === 0 && <span className="text-xs text-brand-400 font-bold mr-1.5">#1</span>}
                      {pr.role}
                    </span>
                    <span className={`font-bold ${i === 0 ? "text-brand-400" : "text-slate-400"}`}>
                      {pr.score}%
                    </span>
                  </div>
                  <div className="progress-bar">
                    <motion.div
                      className="progress-fill"
                      initial={{ width: 0 }}
                      animate={{ width: `${Math.min(pr.score, 100)}%` }}
                      transition={{ duration: 1.1, delay: i * 0.07, ease: "easeOut" }}
                      style={{
                        background: i === 0
                          ? "linear-gradient(90deg,#6366f1,#8b5cf6)"
                          : "linear-gradient(90deg,#334155,#475569)",
                      }}
                    />
                  </div>
                </motion.div>
              ))}
            </div>
            <button
              onClick={() => setShowAllRoles(p => !p)}
              className="mt-4 flex items-center gap-1 text-brand-400 hover:text-brand-300 text-xs font-medium transition-colors"
            >
              {showAllRoles ? <><ChevronUp className="w-3.5 h-3.5" /> Show Less</> : <><ChevronDown className="w-3.5 h-3.5" /> Show All {r.predicted_roles.length} Roles</>}
            </button>
          </SectionCard>

          {/* Skills Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <SectionCard title="Your Skills" icon={CheckCircle2}>
              <div className="flex flex-wrap gap-2">
                {r.skills.length > 0 ? r.skills.map(s => (
                  <span key={s} className="skill-tag present">{s}</span>
                )) : <p className="text-slate-500 text-sm">No skills detected</p>}
              </div>
            </SectionCard>

            <SectionCard title="Missing Skills" icon={AlertTriangle}>
              <div className="flex flex-wrap gap-2">
                {r.missing_skills.length > 0 ? r.missing_skills.map(s => (
                  <span key={s} className="skill-tag missing">{s}</span>
                )) : (
                  <p className="text-emerald-400 text-sm flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4" />
                    All key skills present!
                  </p>
                )}
              </div>
            </SectionCard>
          </div>

          {/* Resume Sections */}
          <SectionCard title="Resume Sections Detected" icon={FileText}>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {Object.entries(r.sections).map(([section, present]) => (
                <div
                  key={section}
                  className={`flex items-center gap-2 px-3 py-2 rounded-xl border text-sm font-medium capitalize ${
                    present
                      ? "bg-emerald-600/10 border-emerald-500/25 text-emerald-400"
                      : "bg-slate-800/40 border-surface-border text-slate-500"
                  }`}
                >
                  {present
                    ? <CheckCircle2 className="w-4 h-4 shrink-0" />
                    : <X className="w-4 h-4 shrink-0" />
                  }
                  {section}
                </div>
              ))}
            </div>
          </SectionCard>

          {/* Courses */}
          {Object.keys(r.courses).length > 0 && (
            <SectionCard title="Recommended Courses" icon={BookOpen}>
              <div className="space-y-4">
                {Object.entries(r.courses).map(([skill, courses]) => (
                  <div key={skill}>
                    <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">{skill}</p>
                    <div className="space-y-1.5">
                      {courses.slice(0, 3).map((c, i) => (
                        <div
                          key={i}
                          className="flex items-center gap-2 px-3 py-2 bg-surface-border/30 rounded-lg text-sm text-slate-300"
                        >
                          <BookOpen className="w-3.5 h-3.5 text-brand-400 shrink-0" />
                          {c}
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </SectionCard>
          )}

          {/* Suggestions */}
          {r.suggestions.length > 0 && (
            <SectionCard title="AI Suggestions" icon={Lightbulb}>
              <ul className="space-y-3">
                {r.suggestions.map((s, i) => (
                  <motion.li
                    key={i}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.08 }}
                    className="flex items-start gap-3 text-sm text-slate-300"
                  >
                    <span className="w-5 h-5 rounded-full bg-brand-600/20 text-brand-400 text-xs flex items-center justify-center shrink-0 mt-0.5">
                      {i + 1}
                    </span>
                    {s}
                  </motion.li>
                ))}
              </ul>
            </SectionCard>
          )}
        </motion.div>
      )}
    </div>
  );
}
