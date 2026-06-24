"use client";

import { useParams, useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import SandboxEditor from "@/components/editor/SandboxEditor";
import { api } from "@/lib/apiClient";

interface LessonContent {
  concept_id: string;
  concept_name: string;
  worked_example: string;
  guided_practice: string;
  exercise_prompt: string;
}

export default function LessonPage() {
  return (
    <Suspense fallback={<p className="text-white/60">Loading...</p>}>
      <LessonPageInner />
    </Suspense>
  );
}

function LessonPageInner() {
  const router = useRouter();
  const params = useParams<{ conceptId: string }>();
  const searchParams = useSearchParams();
  const sessionId = searchParams.get("session") ?? "";

  const [lesson, setLesson] = useState<LessonContent | null>(null);
  const [code, setCode] = useState("");
  const [feedback, setFeedback] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!sessionId || !params.conceptId) return;
    api
      .startLesson(sessionId, params.conceptId)
      .then(setLesson)
      .finally(() => setLoading(false));
  }, [sessionId, params.conceptId]);

  async function handleRun() {
    if (!lesson) return;
    setSubmitting(true);
    setFeedback(null);
    try {
      const res = await api.submitSolution(sessionId, lesson.concept_id, code);
      setStatus(res.status);
      setFeedback(res.hint ?? res.explanation ?? null);
      if (res.status === "pass") {
        if (res.next_concept_id) {
          router.push(`/lesson/${res.next_concept_id}?session=${sessionId}`);
        } else {
          router.push(`/dashboard?session=${sessionId}`);
        }
      }
    } catch (err) {
      setFeedback(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) return <p className="text-white/60">Generating your lesson...</p>;
  if (!lesson) return <p className="text-red-400">Could not load lesson.</p>;

  return (
    <div className="grid md:grid-cols-2 gap-6">
      <div className="space-y-4">
        <h1 className="text-2xl font-semibold">{lesson.concept_name}</h1>

        <section className="bg-surface rounded-xl p-4 border border-white/10">
          <h2 className="text-sm uppercase text-white/50 mb-2">Worked example</h2>
          <pre className="whitespace-pre-wrap text-sm">{lesson.worked_example}</pre>
        </section>

        <section className="bg-surface rounded-xl p-4 border border-white/10">
          <h2 className="text-sm uppercase text-white/50 mb-2">Guided practice</h2>
          <pre className="whitespace-pre-wrap text-sm">{lesson.guided_practice}</pre>
        </section>

        <section className="bg-surface rounded-xl p-4 border border-white/10">
          <h2 className="text-sm uppercase text-white/50 mb-2">Exercise</h2>
          <p className="text-sm">{lesson.exercise_prompt}</p>
        </section>
      </div>

      <div className="space-y-4">
        <SandboxEditor value={code} onChange={setCode} />
        <button
          onClick={handleRun}
          disabled={submitting}
          className="bg-accent text-black font-medium px-4 py-2 rounded-lg disabled:opacity-50"
        >
          {submitting ? "Running..." : "Run"}
        </button>
        {status && status !== "pass" && (
          <div className="bg-surface rounded-xl p-4 border border-white/10">
            <p className="text-xs uppercase text-white/50 mb-1">{status}</p>
            <p className="text-sm whitespace-pre-wrap">{feedback}</p>
          </div>
        )}
      </div>
    </div>
  );
}
