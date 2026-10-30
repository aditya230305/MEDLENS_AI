import React, { useState } from 'react';
import { Copy, Check, FileCheck, Stethoscope } from 'lucide-react';

interface StructuredSummaryProps {
  summaryText: string;
}

export const StructuredSummary: React.FC<StructuredSummaryProps> = ({ summaryText }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(summaryText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Convert simple markdown headings and bullets into styled elements
  const formatMarkdown = (text: string) => {
    const lines = text.split('\n');
    return lines.map((line, idx) => {
      const trimmed = line.trim();

      // Heading 2 (##)
      if (trimmed.startsWith('## ')) {
        return (
          <h3 key={idx} className="text-base font-bold text-slate-900 mt-5 mb-2 flex items-center gap-2 border-b border-slate-200 pb-1">
            {trimmed.replace('## ', '')}
          </h3>
        );
      }

      // Heading 3 (###)
      if (trimmed.startsWith('### ')) {
        return (
          <h4 key={idx} className="text-sm font-bold text-blue-900 mt-3 mb-1">
            {trimmed.replace('### ', '')}
          </h4>
        );
      }

      // Bullet points
      if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
        const content = trimmed.replace(/^[-*]\s+/, '');
        // Bold parsing
        const parts = content.split(/(\*\*.*?\*\*)/g);
        return (
          <li key={idx} className="text-sm text-slate-700 ml-4 list-disc mb-1 leading-relaxed">
            {parts.map((p, pIdx) => {
              if (p.startsWith('**') && p.endsWith('**')) {
                return <strong key={pIdx} className="font-semibold text-slate-900">{p.slice(2, -2)}</strong>;
              }
              if (p.startsWith('`') && p.endsWith('`')) {
                return <code key={pIdx} className="px-1 py-0.5 rounded bg-slate-100 font-mono text-xs text-rose-700">{p.slice(1, -1)}</code>;
              }
              return p;
            })}
          </li>
        );
      }

      // Blockquotes / Callout notes
      if (trimmed.startsWith('> ')) {
        return (
          <div key={idx} className="bg-blue-50 border-l-3 border-blue-500 p-2.5 my-2 rounded-r text-xs text-blue-800 italic">
            {trimmed.replace('> ', '')}
          </div>
        );
      }

      // Horizontal rule
      if (trimmed === '---') {
        return <hr key={idx} className="my-4 border-slate-200" />;
      }

      // Empty line
      if (!trimmed) {
        return <div key={idx} className="h-2" />;
      }

      // Standard text
      return (
        <p key={idx} className="text-sm text-slate-700 leading-relaxed mb-1">
          {trimmed}
        </p>
      );
    });
  };

  return (
    <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm relative">
      <div className="flex items-center justify-between mb-4 border-b border-slate-100 pb-3">
        <div className="flex items-center gap-2">
          <Stethoscope className="w-5 h-5 text-blue-600" />
          <h2 className="text-base font-bold text-slate-900">
            Structured Clinical Summary
          </h2>
          <span className="text-[11px] font-semibold px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200">
            Physician / Clinical Grade
          </span>
        </div>

        <button
          onClick={handleCopy}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 transition-colors"
        >
          {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
          <span>{copied ? 'Copied' : 'Copy Summary'}</span>
        </button>
      </div>

      <div className="prose max-w-none">
        {formatMarkdown(summaryText)}
      </div>
    </div>
  );
};
