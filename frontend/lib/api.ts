// lib/api.ts — Typed API client for the FastAPI backend

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface PredictedRole {
  role: string;
  score: number;
}

export interface AnalysisResult {
  predicted_roles:    PredictedRole[];
  target_match_score: number;
  skills:             string[];
  missing_skills:     string[];
  courses:            Record<string, string[]>;
  ats_score:          number;
  sections:           Record<string, boolean>;
  suggestions:        string[];
}

export interface ChatResponse {
  reply: string;
}

export interface RolesResponse {
  roles: string[];
}

// ── Analyze resume ────────────────────────────────────────────────────────
export async function analyzeResume(
  file: File,
  targetRole: string,
): Promise<AnalysisResult> {
  const form = new FormData();
  form.append("file", file);
  form.append("target_role", targetRole);

  const res = await fetch(`${BASE}/analyze-resume`, {
    method: "POST",
    body: form,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(err.detail ?? "Analysis failed");
  }

  return res.json() as Promise<AnalysisResult>;
}

// ── Roles ──────────────────────────────────────────────────────────────────
export async function fetchRoles(): Promise<string[]> {
  const res = await fetch(`${BASE}/roles`);
  if (!res.ok) {
    throw new Error("Failed to fetch roles");
  }
  const data: RolesResponse = await res.json();
  return data.roles ?? [];
}

// ── Chat ──────────────────────────────────────────────────────────────────
export async function sendChat(
  query: string,
  resumeContext: Partial<AnalysisResult> & { target_role?: string },
): Promise<string> {
  const res = await fetch(`${BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, resume_context: resumeContext }),
  });

  if (!res.ok) throw new Error("Chat request failed");

  const data: ChatResponse = await res.json();
  return data.reply;
}
