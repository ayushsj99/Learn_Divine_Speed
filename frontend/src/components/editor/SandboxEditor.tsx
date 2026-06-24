"use client";

import Editor from "@monaco-editor/react";

interface SandboxEditorProps {
  value: string;
  onChange: (value: string) => void;
}

export default function SandboxEditor({ value, onChange }: SandboxEditorProps) {
  return (
    <div className="rounded-lg overflow-hidden border border-white/10">
      <Editor
        height="320px"
        defaultLanguage="python"
        theme="vs-dark"
        value={value}
        onChange={(v) => onChange(v ?? "")}
        options={{ fontSize: 14, minimap: { enabled: false } }}
      />
    </div>
  );
}
