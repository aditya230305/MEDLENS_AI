import React, { useState } from 'react';
import { HeartHandshake, Copy, Check, MessageCircle, HelpCircle } from 'lucide-react';

interface PatientExplanationProps {
  explanationText: string;
}

export const PatientExplanation: React.FC<PatientExplanationProps> = ({ explanationText }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(explanationText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const formatMarkdown = (text: string) => {
    const lines = text.split('\n');
    return lines.map((line, idx) => {
      const trimmed = line.trim();

      if (trimmed.startsWith('## ')) {
        return (
          <h3 key={idx} className="text-base font-bold text-slate-900 mt-5 mb-2.5 flex items-center gap-2 border-b border-slate-100 pb-1.5">
            {trimmed.replace('## ', '')}
          </h3>
        );
      }

      if (trimmed.startsWith('### ')) {
        return (
          <h4 key={idx} className="text-sm font-bold text-emerald-800 mt-3 mb-1">
            {trimmed.replace('### ', '')}
          </h4>
        );
      }

      if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
        const content = trimmed.replace(/^[-*]\s+/, '');
        const parts = content.split(/(\*\*.*?\*\*)/g);
        return (
          <li key={idx} className="text-sm text-slate-700 ml-4 list-disc mb-1.5 leading-relaxed">
            {parts.map((p, pIdx) => {
              if (p.startsWith('**') && p.endsWith('**')) {
                return <strong key={pIdx} className="font-semibold text-slate-900">{p.slice(2, -2)}</strong>;
              }
              return p;
            })}
          </li>
        );
      }

      if (trimmed.startsWith('> ')) {
        return (
          <div key={idx} className="bg-emerald-50 border-l-3 border-emerald-500 p-2.5 my-2 rounded-r text-xs text-emerald-800 italic">
            {trimmed.replace('> ', '')}
          </div>
        );
      }

      if (trimmed === '---') {
        return <hr key={idx} className="my-4 border-slate-200" />;
      }

      if (!trimmed) {
        return <div key={idx} className="h-2" />;
      }

      return (
        <p key={idx} className="text-sm text-slate-700 leading-relaxed mb-2">
          {trimmed}
        </p>
      );
    });
  };

  return (
    <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm relative">
      <div className="flex items-center justify-between mb-4 border-b border-slate-100 pb-3">
        <div className="flex items-center gap-2">
          <HeartHandshake className="w-5 h-5 text-emerald-600" />
          <h2 className="text-base font-bold text-slate-900">
            Patient-Friendly Plain Language Guide
          </h2>
          <span className="text-[11px] font-semibold px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">
            Demystified Medical Jargon
          </span>
        </div>

        <button
          onClick={handleCopy}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 transition-colors"
        >
          {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
          <span>{copied ? 'Copied' : 'Copy Guide'}</span>
        </button>
      </div>

      <div className="prose max-w-none">
        {formatMarkdown(explanationText)}
      </div>
    </div>
  );
};
