"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { api, Syllabus } from "@/lib/apiClient";

export default function SyllabusPage() {
  return (
    <Suspense fallback={<p className="text-white/60">Loading...</p>}>
      <SyllabusPageInner />
    </Suspense>
  );
}

function SyllabusPageInner() {
  const searchParams = useSearchParams();
  const sessionId = searchParams.get("session") ?? "";

  const [syllabus, setSyllabus] = useState<Syllabus | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!sessionId) return;
    let attempts = 0;
    const poll = setInterval(async () => {
      attempts += 1;
      try {
        const data = await api.getSyllabus(sessionId);
        setSyllabus(data);
        clearInterval(poll);
      } catch (err) {
        if (attempts > 15) {
          setError(err instanceof Error ? err.message : "Syllabus build timed out.");
          clearInterval(poll);
        }
      }
    }, 2000);
    return () => clearInterval(poll);
  }, [sessionId]);

  if (error) return <p className="text-red-400">{error}</p>;
  if (!syllabus) return <p className="text-white/60">Building your syllabus...</p>;

  const firstPending = syllabus.concepts.find((c) => c.status !== "completed");

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Your syllabus: {syllabus.framework}</h1>
      <ol className="space-y-3">
        {syllabus.concepts.map((concept) => (
          <li key={concept.id} className="bg-surface rounded-xl p-4 border border-white/10">
            <div className="flex items-center justify-between">
              <span className="font-medium">
                {concept.ordinal + 1}. {concept.name}
              </span>
              <span className="text-xs uppercase text-white/50">{concept.status}</span>
            </div>
            <p className="text-white/60 text-sm mt-1">{concept.description}</p>
            {concept.prereq_concept_ids.length > 0 && (
              <p className="text-xs text-white/40 mt-1">Has prerequisites</p>
            )}
          </li>
        ))}
      </ol>
      {firstPending && (
        <Link
          href={`/lesson/${firstPending.id}?session=${sessionId}`}
          className="inline-block bg-accent text-black font-medium px-4 py-2 rounded-lg"
        >
          Start: {firstPending.name}
        </Link>
      )}
    </div>
  );
}
