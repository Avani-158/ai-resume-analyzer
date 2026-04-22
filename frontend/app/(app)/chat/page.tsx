"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useAppState } from "@/lib/store";
import { sendChat } from "@/lib/api";
import { MessageSquare, Send, Loader2, BrainCircuit, User } from "lucide-react";

interface Message {
  role: "user" | "assistant";
  content: string;
  ts: number;
}

const STARTERS = [
  "What skills am I missing?",
  "How can I improve my ATS score?",
  "What projects should I build?",
  "How do I prepare for interviews?",
];

export default function ChatPage() {
  const { state } = useAppState();
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: state.results
        ? `Hi! I've analyzed your resume. Your ATS score is **${state.results.ats_score}/100** and your match score is **${state.results.target_match_score}%**. What would you like to know?`
        : "Hi! I'm your AI career assistant. Upload a resume first for personalized advice, or ask me anything about career development!",
      ts: Date.now(),
    },
  ]);
  const [input, setInput]   = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = async (text?: string) => {
    const query = (text ?? input).trim();
    if (!query || loading) return;
    setInput("");

    const userMsg: Message = { role: "user", content: query, ts: Date.now() };
    setMessages(prev => [...prev, userMsg]);
    setLoading(true);

    try {
      const ctx = state.results
        ? { ...state.results, target_role: state.targetRole }
        : { target_role: state.targetRole };

      const reply = await sendChat(query, ctx);
      setMessages(prev => [...prev, { role: "assistant", content: reply, ts: Date.now() }]);
    } catch {
      setMessages(prev => [
        ...prev,
        { role: "assistant", content: "Sorry, I couldn't connect to the server. Please try again.", ts: Date.now() },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const formatContent = (text: string) =>
    text.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");

  return (
    <div className="p-8 max-w-3xl flex flex-col" style={{ height: "calc(100vh - 0px)" }}>
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: -12 }} animate={{ opacity: 1, y: 0 }} className="mb-6 shrink-0">
        <h1 className="text-3xl font-extrabold text-white mb-1 flex items-center gap-3">
          <MessageSquare className="w-8 h-8 text-brand-400" />
          AI Career Assistant
        </h1>
        <p className="text-slate-400 text-sm">
          Ask anything about your resume, career path, or skills.
          {state.results && (
            <span className="ml-2 inline-flex items-center gap-1 text-emerald-400 text-xs font-medium">
              <span className="w-1.5 h-1.5 bg-emerald-400 rounded-full" />
              Resume context loaded
            </span>
          )}
        </p>
      </motion.div>

      {/* Message area */}
      <div className="flex-1 overflow-y-auto space-y-4 pr-1 mb-4 min-h-0">
        <AnimatePresence initial={false}>
          {messages.map((msg, i) => (
            <motion.div
              key={msg.ts}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.05 * Math.min(i, 3) }}
              className={`flex gap-3 ${msg.role === "user" ? "flex-row-reverse" : ""}`}
            >
              {/* Avatar */}
              <div className={`w-8 h-8 rounded-full shrink-0 flex items-center justify-center ${
                msg.role === "assistant"
                  ? "bg-brand-600/25 text-brand-400"
                  : "bg-slate-700 text-slate-300"
              }`}>
                {msg.role === "assistant"
                  ? <BrainCircuit className="w-4 h-4" />
                  : <User className="w-4 h-4" />
                }
              </div>

              {/* Bubble */}
              <div className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                msg.role === "assistant"
                  ? "glass text-slate-200"
                  : "bg-brand-600 text-white"
              }`}>
                <p dangerouslySetInnerHTML={{ __html: formatContent(msg.content) }} />
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {/* Loading bubble */}
        {loading && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex gap-3">
            <div className="w-8 h-8 rounded-full bg-brand-600/25 text-brand-400 flex items-center justify-center">
              <BrainCircuit className="w-4 h-4" />
            </div>
            <div className="glass rounded-2xl px-4 py-3">
              <Loader2 className="w-4 h-4 animate-spin text-brand-400" />
            </div>
          </motion.div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Starters */}
      {messages.length <= 1 && (
        <div className="flex flex-wrap gap-2 mb-4 shrink-0">
          {STARTERS.map(s => (
            <button
              key={s}
              onClick={() => send(s)}
              className="text-xs px-3 py-1.5 rounded-full border border-surface-border text-slate-400 hover:border-brand-500/40 hover:text-brand-300 transition-all"
            >
              {s}
            </button>
          ))}
        </div>
      )}

      {/* Input */}
      <div className="glass rounded-2xl p-2 flex gap-2 shrink-0">
        <input
          id="chat-input"
          type="text"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === "Enter" && !e.shiftKey && send()}
          placeholder="Ask about your career, skills, or resume…"
          className="flex-1 bg-transparent px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none"
        />
        <button
          id="chat-send-btn"
          onClick={() => send()}
          disabled={loading || !input.trim()}
          className="w-10 h-10 rounded-xl bg-brand-600 hover:bg-brand-500 disabled:opacity-40 disabled:cursor-not-allowed text-white flex items-center justify-center transition-all"
        >
          <Send className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
