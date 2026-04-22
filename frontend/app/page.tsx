"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import {
  BrainCircuit,
  UploadCloud,
  Sparkles,
  BarChart3,
  BookOpen,
  Shield,
  ArrowRight,
  CheckCircle2,
} from "lucide-react";

const features = [
  { icon: BrainCircuit,  title: "AI Role Matching",     desc: "Sentence-transformer embeddings match your profile to 1000+ job roles with hybrid scoring." },
  { icon: BarChart3,     title: "ATS Score",            desc: "Know exactly how recruiters' systems rank your resume before you even apply." },
  { icon: Sparkles,      title: "Skill Gap Analysis",   desc: "Instantly see what skills you're missing and get curated course recommendations." },
  { icon: BookOpen,      title: "Course Guidance",      desc: "Personalized learning paths mapped to your target role and current skill set." },
  { icon: Shield,        title: "Section Detection",    desc: "Automatic parsing of projects, education, experience, and certifications." },
  { icon: UploadCloud,   title: "Instant Processing",   desc: "Upload a PDF and get a complete analysis in seconds — no account needed." },
];

const steps = [
  { n: "01", t: "Upload Resume",     d: "Drop your PDF resume — we handle the parsing." },
  { n: "02", t: "Set Target Role",   d: "Tell us the job title you're aiming for." },
  { n: "03", t: "Get AI Analysis",   d: "Receive match scores, skill gaps, and ATS rating." },
  { n: "04", t: "Take Action",       d: "Follow course recommendations and chat with AI." },
];

const stats = [
  { n: "1000+", l: "Job Roles" },
  { n: "50+",   l: "Skills Tracked" },
  { n: "98%",   l: "Parse Accuracy" },
  { n: "< 5s",  l: "Analysis Time" },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-surface">
      {/* ── Nav ─────────────────────────────────────────── */}
      <nav className="fixed top-0 inset-x-0 z-50 border-b border-surface-border/50 backdrop-blur-xl bg-surface/70">
        <div className="max-w-7xl mx-auto px-6 flex items-center justify-between h-16">
          <div className="flex items-center gap-2">
            <BrainCircuit className="w-7 h-7 text-brand-400" />
            <span className="font-bold text-lg gradient-text">ResumeAI</span>
          </div>
          <div className="flex items-center gap-4">
            <Link href="/dashboard" className="text-slate-400 hover:text-white text-sm transition-colors">
              Dashboard
            </Link>
            <Link
              href="/analyzer"
              className="bg-brand-600 hover:bg-brand-500 text-white text-sm font-semibold px-5 py-2 rounded-xl transition-all duration-200 hover:shadow-lg hover:shadow-brand-600/25"
            >
              Analyze Resume
            </Link>
          </div>
        </div>
      </nav>

      {/* ── Hero ────────────────────────────────────────── */}
      <section className="relative pt-36 pb-24 px-6 overflow-hidden">
        <div className="absolute inset-0 bg-hero-glow pointer-events-none" />
        {/* Floating orbs */}
        <div className="absolute top-20 left-1/4 w-72 h-72 bg-brand-600/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute top-40 right-1/4 w-64 h-64 bg-purple-600/10 rounded-full blur-3xl pointer-events-none" />

        <div className="max-w-4xl mx-auto text-center relative">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="inline-flex items-center gap-2 bg-brand-600/15 border border-brand-500/25 text-brand-300 text-xs font-semibold px-4 py-2 rounded-full mb-8"
          >
            <Sparkles className="w-3.5 h-3.5" />
            Powered by Sentence Transformers + ML Pipeline
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="text-5xl md:text-7xl font-extrabold tracking-tight mb-6 leading-tight"
          >
            Your Resume,{" "}
            <span className="gradient-text">Analyzed by AI</span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="text-slate-400 text-lg md:text-xl max-w-2xl mx-auto mb-10 leading-relaxed"
          >
            Upload your resume, set your target role, and get an instant AI-driven
            analysis with skill gaps, ATS scores, and a personalized roadmap.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="flex flex-col sm:flex-row gap-4 justify-center"
          >
            <Link
              href="/analyzer"
              id="hero-cta-analyze"
              className="group flex items-center justify-center gap-2 bg-brand-600 hover:bg-brand-500 text-white font-bold px-8 py-4 rounded-2xl transition-all duration-200 hover:shadow-xl hover:shadow-brand-600/30 hover:-translate-y-0.5"
            >
              <UploadCloud className="w-5 h-5" />
              Analyze My Resume
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </Link>
            <Link
              href="/employer"
              id="hero-cta-employer"
              className="flex items-center justify-center gap-2 border border-surface-border hover:border-brand-500/40 text-slate-300 hover:text-white font-semibold px-8 py-4 rounded-2xl transition-all duration-200"
            >
              Employer Panel
            </Link>
          </motion.div>
        </div>
      </section>

      {/* ── Stats ───────────────────────────────────────── */}
      <section className="py-12 border-y border-surface-border/40">
        <div className="max-w-5xl mx-auto px-6 grid grid-cols-2 md:grid-cols-4 gap-8">
          {stats.map((s, i) => (
            <motion.div
              key={s.l}
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              className="text-center"
            >
              <div className="text-3xl font-extrabold gradient-text">{s.n}</div>
              <div className="text-slate-500 text-sm mt-1">{s.l}</div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ── Features ────────────────────────────────────── */}
      <section className="py-24 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-14">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              Everything You Need to Land the Role
            </h2>
            <p className="text-slate-400 max-w-xl mx-auto">
              A complete ML-powered career toolkit — no fluff, just real signal.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((f, i) => (
              <motion.div
                key={f.title}
                initial={{ opacity: 0, y: 24 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.08 }}
                className="glass rounded-2xl p-6 hover:border-brand-500/30 transition-colors duration-300 bg-card-glow"
              >
                <div className="w-11 h-11 rounded-xl bg-brand-600/20 flex items-center justify-center mb-4">
                  <f.icon className="w-5 h-5 text-brand-400" />
                </div>
                <h3 className="font-semibold text-white mb-2">{f.title}</h3>
                <p className="text-slate-400 text-sm leading-relaxed">{f.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ── How it works ────────────────────────────────── */}
      <section className="py-24 px-6 bg-surface-card/40">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-14">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">How It Works</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            {steps.map((s, i) => (
              <motion.div
                key={s.n}
                initial={{ opacity: 0, x: -16 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                className="glass rounded-2xl p-6 text-center"
              >
                <div className="text-4xl font-extrabold gradient-text mb-3">{s.n}</div>
                <div className="font-semibold text-white mb-2">{s.t}</div>
                <p className="text-slate-400 text-sm">{s.d}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA ─────────────────────────────────────────── */}
      <section className="py-24 px-6">
        <div className="max-w-3xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, scale: 0.96 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            className="glass rounded-3xl p-12"
          >
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              Ready to <span className="gradient-text">Level Up</span> Your Career?
            </h2>
            <p className="text-slate-400 mb-8">
              Join thousands of candidates who got clarity on their career path.
            </p>
            <div className="flex flex-col sm:flex-row gap-3 justify-center mb-6">
              {["No account required", "Instant results", "100% private"].map(t => (
                <span key={t} className="flex items-center gap-1.5 text-sm text-slate-400">
                  <CheckCircle2 className="w-4 h-4 text-brand-400 shrink-0" />
                  {t}
                </span>
              ))}
            </div>
            <Link
              href="/analyzer"
              id="bottom-cta"
              className="inline-flex items-center gap-2 bg-brand-600 hover:bg-brand-500 text-white font-bold px-10 py-4 rounded-2xl transition-all hover:shadow-xl hover:shadow-brand-600/30 hover:-translate-y-0.5"
            >
              Start Free Analysis
              <ArrowRight className="w-5 h-5" />
            </Link>
          </motion.div>
        </div>
      </section>

      {/* ── Footer ──────────────────────────────────────── */}
      <footer className="border-t border-surface-border/40 py-8 px-6 text-center text-slate-500 text-sm">
        <div className="flex items-center justify-center gap-2 mb-2">
          <BrainCircuit className="w-4 h-4 text-brand-400" />
          <span className="font-semibold text-slate-300">ResumeAI</span>
        </div>
        Built with FastAPI · Next.js · Sentence Transformers
      </footer>
    </div>
  );
}
