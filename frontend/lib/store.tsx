// lib/store.ts — Lightweight Zustand-free global state via React Context + useReducer

"use client";

import { createContext, useContext, useReducer, ReactNode } from "react";
import { AnalysisResult } from "./api";

// ── State shape ───────────────────────────────────────────────────────────

interface AppState {
  targetRole:  string;
  uploadedFile: File | null;
  results:     AnalysisResult | null;
  loading:     boolean;
  error:       string | null;
}

const initialState: AppState = {
  targetRole:   "",
  uploadedFile: null,
  results:      null,
  loading:      false,
  error:        null,
};

// ── Actions ───────────────────────────────────────────────────────────────

type Action =
  | { type: "SET_ROLE";    payload: string }
  | { type: "SET_FILE";    payload: File | null }
  | { type: "SET_LOADING"; payload: boolean }
  | { type: "SET_RESULTS"; payload: AnalysisResult }
  | { type: "SET_ERROR";   payload: string | null }
  | { type: "RESET" };

function reducer(state: AppState, action: Action): AppState {
  switch (action.type) {
    case "SET_ROLE":    return { ...state, targetRole: action.payload };
    case "SET_FILE":    return { ...state, uploadedFile: action.payload };
    case "SET_LOADING": return { ...state, loading: action.payload };
    case "SET_RESULTS": return { ...state, results: action.payload, loading: false, error: null };
    case "SET_ERROR":   return { ...state, error: action.payload, loading: false };
    case "RESET":       return initialState;
    default:            return state;
  }
}

// ── Context ───────────────────────────────────────────────────────────────

const AppContext = createContext<{
  state: AppState;
  dispatch: React.Dispatch<Action>;
} | null>(null);

export function AppProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(reducer, initialState);
  return (
    <AppContext.Provider value={{ state, dispatch }}>
      {children}
    </AppContext.Provider>
  );
}

export function useAppState() {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error("useAppState must be inside AppProvider");
  return ctx;
}
