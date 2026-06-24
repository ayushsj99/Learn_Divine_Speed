"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { api } from "@/lib/apiClient";

export default function IntakePage() {
  const router = useRouter();
  const [framework, setFramework] = useState("");
  const [goal, setGoal] = useState("apply_to_project");
  const [goalContext, setGoalContext] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!framework.trim()) {
      setError("Enter the framework or library you want to learn.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const { session_id } = await api.createSession(
        framework.trim(),
        goal,
        goalContext ? { notes: [goalContext] } : undefined
      );
      router.push(`/diagnostic?session=${session_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">What do you want to learn?</h1>
        <p className="text-white/60 mt-1">
          Any framework or library — we&apos;ll diagnose your real level and build a syllabus around your goal.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5 bg-surface rounded-xl p-6 border border-white/10">
        <div>
          <label className="block text-sm text-white/70 mb-1">Framework / library</label>
          <input
            value={framework}
            onChange={(e) => setFramework(e.target.value)}
            placeholder="e.g. FastAPI, React, pandas..."
            className="w-full rounded-lg bg-black/30 border border-white/10 px-3 py-2 outline-none focus:border-accent"
          />
        </div>

        <div>
          <label className="block text-sm text-white/70 mb-1">Why are you learning it?</label>
          <select
            value={goal}
            onChange={(e) => setGoal(e.target.value)}
            className="w-full rounded-lg bg-black/30 border border-white/10 px-3 py-2 outline-none focus:border-accent"
          >
            <option value="apply_to_project">Apply it to a project</option>
            <option value="interview_prep">Prepare for an interview</option>
            <option value="understand_only">Just understand what it is</option>
          </select>
        </div>

        <div>
          <label className="block text-sm text-white/70 mb-1">Context (optional)</label>
          <textarea
            value={goalContext}
            onChange={(e) => setGoalContext(e.target.value)}
            placeholder="e.g. building a CLI tool that talks to a REST API"
            className="w-full rounded-lg bg-black/30 border border-white/10 px-3 py-2 outline-none focus:border-accent"
            rows={2}
          />
        </div>

        {error && <p className="text-red-400 text-sm">{error}</p>}

        <button
          type="submit"
          disabled={loading}
          className="bg-accent text-black font-medium px-4 py-2 rounded-lg disabled:opacity-50"
        >
          {loading ? "Starting..." : "Start learning"}
        </button>
      </form>
    </div>
  );
}
