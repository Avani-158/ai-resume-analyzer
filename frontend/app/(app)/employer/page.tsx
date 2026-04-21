"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { analyzeResume, AnalysisResult } from "@/lib/api";
import toast from "react-hot-toast";
import { Users, UploadCloud, Loader2, ChevronUp, ChevronDown, X, Sparkles, BarChart3 } from "lucide-react";

interface Candidate {
  name: string;
  score: number;
  ats: number;
  skills: string[];
  missing: number;
}

export default function EmployerPage() {
  const [jobRole, setJobRole]       = useState("");
  const [files, setFiles]           = useState<File[]>([]);
  const [loading, setLoading]       = useState(false);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [sortBy, setSortBy]         = useState<"score" | "ats">("score");
  const [sortDir, setSortDir]       = useState<"desc" | "asc">("desc");

  const handleFiles = (incoming: FileList | null) => {
    if (!incoming) return;
    const pdfs = Array.from(incoming).filter(f => f.name.toLowerCase().endsWith(".pdf"));
    if (pdfs.length !== incoming.length) toast.error("Only PDF files are accepted");
    setFiles(prev => [...prev, ...pdfs]);
  };

  const removeFile = (i: number) => setFiles(prev => prev.filter((_, idx) => idx !== i));

  const handleAnalyzeAll = async () => {
    if (!jobRole)       return toast.error("Enter a job role first");
    if (!files.length)  return toast.error("Upload at least one resume");

    setLoading(true);
    const results: Candidate[] = [];

    for (const file of files) {
      try {
        const res: AnalysisResult = await analyzeResume(file, jobRole);
        results.push({
          name:    file.name.replace(".pdf", ""),
          score:   res.target_match_score,
          ats:     res.ats_score,
          skills:  res.skills,
          missing: res.missing_skills.length,
        });
      } catch {
        toast.error(`Failed to analyze ${file.name}`);
      }
    }

    setCandidates(results);
    setLoading(false);
    if (results.length) toast.success(`Analyzed ${results.length} resumes ✓`);
  };

  const sorted = [...candidates].sort((a, b) => {
    const diff = a[sortBy] - b[sortBy];
    return sortDir === "desc" ? -diff : diff;
  });

  const toggle = (col: "score" | "ats") => {
    if (sortBy === col) setSortDir(d => d === "desc" ? "asc" : "desc");
    else { setSortBy(col); setSortDir("desc"); }
  };

  const Icon = ({ col }: { col: "score" | "ats" }) =>
    sortBy === col
      ? (sortDir === "desc" ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronUp className="w-3.5 h-3.5" />)
      : null;

  return (
    <div className="p-8 max-w-5xl">
      <motion.div initial={{ opacity: 0, y: -12 }} animate={{ opacity: 1, y: 0 }} className="mb-8">
        <h1 className="text-3xl font-extrabold text-white mb-1 flex items-center gap-3">
          <Users className="w-8 h-8 text-brand-400" />
          Employer Panel
        </h1>
        <p className="text-slate-400 text-sm">
          Upload multiple resumes and rank candidates against a job role.
        </p>
      </motion.div>

      {/* Config */}
      <div className="glass rounded-2xl p-6 mb-6 space-y-5">
        <div>
          <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
            Job Role
          </label>
          <input
            id="employer-role-input"
            type="text"
            value={jobRole}
            onChange={e => setJobRole(e.target.value)}
            placeholder="e.g. Data Scientist"
            className="w-full bg-surface-border/40 border border-surface-border rounded-xl px-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:border-brand-500 text-sm"
          />
        </div>

        {/* Multi-upload */}
        <div>
          <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
            Resumes (PDF)
          </label>
          <label
            htmlFor="employer-file-input"
            className="flex items-center justify-center gap-3 border-2 border-dashed border-surface-border hover:border-brand-500/50 rounded-2xl p-6 cursor-pointer transition-all hover:bg-surface-hover"
          >
            <UploadCloud className="w-6 h-6 text-slate-500" />
            <span className="text-slate-400 text-sm">
              <span className="text-brand-400 font-semibold">Click to add resumes</span> — multiple allowed
            </span>
            <input
              id="employer-file-input"
              type="file"
              accept=".pdf"
              multiple
              className="hidden"
              onChange={e => handleFiles(e.target.files)}
            />
          </label>
        </div>

        {/* File list */}
        <AnimatePresence>
          {files.length > 0 && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-2">
              {files.map((f, i) => (
                <div key={i} className="flex items-center justify-between bg-surface-border/30 rounded-xl px-4 py-2.5 text-sm text-slate-300">
                  <span className="truncate max-w-xs">{f.name}</span>
                  <button onClick={() => removeFile(i)} className="text-slate-500 hover:text-red-400 transition-colors ml-3">
                    <X className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </motion.div>
          )}
        </AnimatePresence>

        <button
          id="employer-analyze-btn"
          onClick={handleAnalyzeAll}
          disabled={loading}
          className="flex items-center gap-2 bg-brand-600 hover:bg-brand-500 disabled:opacity-60 text-white font-bold px-6 py-3 rounded-xl transition-all"
        >
          {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Sparkles className="w-5 h-5" />}
          {loading ? `Analyzing ${files.length} resumes…` : "Rank Candidates"}
        </button>
      </div>

      {/* Results Table */}
      <AnimatePresence>
        {sorted.length > 0 && (
          <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} className="glass rounded-2xl overflow-hidden">
            <div className="px-6 py-4 border-b border-surface-border flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-brand-400" />
              <h2 className="font-bold text-white">Candidate Rankings</h2>
              <span className="ml-auto text-xs text-slate-500">{sorted.length} candidates</span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-surface-border text-slate-400 text-xs uppercase tracking-wider">
                    <th className="px-6 py-3 text-left font-semibold">Rank</th>
                    <th className="px-6 py-3 text-left font-semibold">Candidate</th>
                    <th className="px-6 py-3 text-left font-semibold cursor-pointer hover:text-white" onClick={() => toggle("score")}>
                      <span className="flex items-center gap-1">Match Score <Icon col="score" /></span>
                    </th>
                    <th className="px-6 py-3 text-left font-semibold cursor-pointer hover:text-white" onClick={() => toggle("ats")}>
                      <span className="flex items-center gap-1">ATS Score <Icon col="ats" /></span>
                    </th>
                    <th className="px-6 py-3 text-left font-semibold">Skills</th>
                    <th className="px-6 py-3 text-left font-semibold">Gaps</th>
                  </tr>
                </thead>
                <tbody>
                  {sorted.map((c, i) => (
                    <motion.tr
                      key={c.name}
                      initial={{ opacity: 0, x: -8 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.05 }}
                      className="border-b border-surface-border/50 hover:bg-surface-hover transition-colors"
                    >
                      <td className="px-6 py-4">
                        <span className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold ${
                          i === 0 ? "bg-brand-600/30 text-brand-300"
                          : i === 1 ? "bg-slate-600/30 text-slate-300"
                          : "bg-surface-border text-slate-400"
                        }`}>#{i + 1}</span>
                      </td>
                      <td className="px-6 py-4 text-white font-medium">{c.name}</td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          <div className="w-20 progress-bar">
                            <div className="progress-fill" style={{ width: `${Math.min(c.score, 100)}%` }} />
                          </div>
                          <span className="text-brand-400 font-bold">{c.score}%</span>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span className={`font-bold ${c.ats >= 75 ? "text-emerald-400" : c.ats >= 50 ? "text-yellow-400" : "text-red-400"}`}>
                          {c.ats}/100
                        </span>
                      </td>
                      <td className="px-6 py-4 text-slate-400">{c.skills.length}</td>
                      <td className="px-6 py-4">
                        <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${
                          c.missing === 0 ? "bg-emerald-600/20 text-emerald-400"
                          : c.missing <= 2 ? "bg-yellow-600/20 text-yellow-400"
                          : "bg-red-600/20 text-red-400"
                        }`}>
                          {c.missing} missing
                        </span>
                      </td>
                    </motion.tr>
                  ))}
                </tbody>
              </table>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
