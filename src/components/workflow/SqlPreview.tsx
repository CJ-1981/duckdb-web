import React from 'react';

export function SqlPreview({ sql }: { sql: string }) {
  if (!sql) return null;
  return (
    <div className="mt-3">
      <label className="flex items-center gap-1.5 text-xs font-semibold text-[#6B778C] mb-1">
        <span className="inline-block w-2 h-2 rounded-full bg-green-400" />
        Generated SQL Preview
      </label>
      <pre data-testid="sql-preview" className="bg-[#1E1E2E] text-[#CDD6F4] text-[11px] rounded-md p-3 font-mono overflow-x-auto whitespace-pre-wrap leading-relaxed">{sql}</pre>
    </div>
  );
}
