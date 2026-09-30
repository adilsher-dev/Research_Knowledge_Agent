"use client";
import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { DocumentItem } from "@/lib/types";

export function useDocuments() {
  const [docs, setDocs] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const load = useCallback(async () => {
    setLoading(true); setError(null);
    try { setDocs(await api.documents()); }
    catch (e) { setError(e instanceof Error ? e.message : "Could not load documents."); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { void load(); }, [load]);
  return { docs, loading, error, reload: load };
}
