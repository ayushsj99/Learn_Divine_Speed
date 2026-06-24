"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { api } from "@/lib/apiClient";

export default function DiagnosticPage() {
  return (
    <Suspense fallback={<p className="text-white/60">Loading...</p>}>
      <DiagnosticPageInner />
    </Suspense>
  );
}

function DiagnosticPageInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const sessionId = searchParams.get("session") ?? "";

  const [question, setQuestion] = useState<string | null>(null);
  const [answer, setAnswer] = useState("");
  const [levelAssigned, setLevelAssigned] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!sessionId) return;
    api
      .submitDiagnosticAnswer(sessionId, null)
      .then((res) => setQuestion(res.next_question ?? null))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [sessionId]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await api.submitDiagnosticAnswer(sessionId, answer);
      setAnswer("");
      if (res.level_assigned) {
        setLevelAssigned(res.level_assigned);
      } else {
        setQuestion(res.next_question ?? null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  if (levelAssigned) {
    return (
      <div className="bg-surface rounded-xl p-6 border border-white/10 space-y-4">
        <h2 className="text-xl font-semibold">Level assigned: {levelAssigned}</h2>
        <p className="text-white/60">Building your syllabus now.</p>
        <button
          onClick={() => router.push(`/syllabus?session=${sessionId}`)}
          className="bg-accent text-black font-medium px-4 py-2 rounded-lg"
        >
          View syllabus
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Quick diagnostic</h1>
      <p className="text-white/60">A few questions so we calibrate to your real level, not a self-rating.</p>

      <div className="bg-surface rounded-xl p-6 border border-white/10 space-y-4">
        {loading && !question ? (
          <p className="text-white/60">Loading question...</p>
        ) : (
          <>
            <p className="text-lg">{question}</p>
            <form onSubmit={handleSubmit} className="space-y-3">
              <textarea
                value={answer}
                onChange={(e) => setAnswer(e.target.value)}
                rows={3}
                className="w-full rounded-lg bg-black/30 border border-white/10 px-3 py-2 outline-none focus:border-accent"
                placeholder="Your answer..."
              />
              {error && <p className="text-red-400 text-sm">{error}</p>}
              <button
                type="submit"
                disabled={loading}
                className="bg-accent text-black font-medium px-4 py-2 rounded-lg disabled:opacity-50"
              >
                {loading ? "Submitting..." : "Submit answer"}
              </button>
            </form>
          </>
        )}
      </div>
    </div>
  );
}
