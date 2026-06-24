"use client";

import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { api, MasteryEntry } from "@/lib/apiClient";

export default function DashboardPage() {
  return (
    <Suspense fallback={<p className="text-white/60">Loading...</p>}>
      <DashboardPageInner />
    </Suspense>
  );
}

function DashboardPageInner() {
  const searchParams = useSearchParams();
  const sessionId = searchParams.get("session") ?? "";

  const [entries, setEntries] = useState<MasteryEntry[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!sessionId) return;
    api.getMastery(sessionId).then(setEntries).catch((err) => setError(err.message));
  }, [sessionId]);

  if (!sessionId) return <p className="text-white/60">Start a session from the home page first.</p>;
  if (error) return <p className="text-red-400">{error}</p>;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Your progress</h1>
      {entries.length === 0 ? (
        <p className="text-white/60">No concepts attempted yet.</p>
      ) : (
        <ul className="space-y-3">
          {entries.map((entry) => (
            <li
              key={entry.id}
              className="bg-surface rounded-xl p-4 border border-white/10 flex items-center justify-between"
            >
              <div>
                <p className="font-medium">Concept {entry.concept_id.slice(0, 8)}</p>
                <p className="text-sm text-white/60">
                  Score {Math.round(entry.mastery_score * 100)}% · {entry.attempts} attempt(s)
                </p>
              </div>
              {entry.shaky_flag && (
                <span className="text-xs bg-yellow-500/20 text-yellow-300 px-2 py-1 rounded-full">shaky</span>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
