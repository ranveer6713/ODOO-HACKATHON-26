"use client";

import { useCallback, useEffect, useState } from "react";
import { clearSession, getSession, setSession, type Session } from "./session";

export function useSession() {
  const [session, setSessionState] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const sync = () => {
      setSessionState(getSession());
      setLoading(false);
    };
    sync();
    window.addEventListener("assetflow:session", sync);
    window.addEventListener("storage", sync);
    return () => {
      window.removeEventListener("assetflow:session", sync);
      window.removeEventListener("storage", sync);
    };
  }, []);

  const login = useCallback((next: Session) => {
    setSession(next);
    setSessionState(next);
  }, []);

  const logout = useCallback(() => {
    clearSession();
    setSessionState(null);
  }, []);

  return { session, loading, login, logout };
}
