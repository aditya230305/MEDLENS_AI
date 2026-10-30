import React from 'react';
import { Check, Clock } from 'lucide-react';
import { PipelineLatencies } from '../types';

interface PipelineStepperProps {
  currentStage: number; // 0 = idle, 1..6 = in progress, 7 = completed
  latencies?: PipelineLatencies;
  isProcessing: boolean;
}

const STAGES = [
  { id: 1, name: 'Ingestion & Routing', desc: 'Format check & text routing' },
  { id: 2, name: 'OCR / Extraction', desc: 'Direct PDF or Tesseract OCR' },
  { id: 3, name: 'Medical NLP', desc: 'Entity extraction & range parsing' },
  { id: 4, name: 'RAG Knowledge', desc: 'Semantic retrieval from DB' },
  { id: 5, name: 'LLM Generation', desc: 'Clinical & patient summaries' },
  { id: 6, name: 'Guardrail Audit', desc: 'Factual consistency & validation' }
];

export const PipelineStepper: React.FC<PipelineStepperProps> = ({
  currentStage,
  latencies,
  isProcessing
}) => {
  return (
    <div className="bg-white p-4 sm:p-5 rounded-xl border border-slate-200 shadow-xs mb-6">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
          Modular Processing Pipeline
        </span>
        {latencies && latencies.total_pipeline_ms > 0 && (
          <span className="text-xs font-semibold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200 flex items-center gap-1">
            <Clock className="w-3.5 h-3.5" />
            Total Pipeline: {latencies.total_pipeline_ms} ms
          </span>
        )}
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        {STAGES.map((s) => {
          const isDone = currentStage > s.id || currentStage === 7;
          const isActive = isProcessing && currentStage === s.id;

          let badgeColor = 'bg-slate-100 text-slate-500 border-slate-200';
          if (isDone) {
            badgeColor = 'bg-emerald-50 border-emerald-300 text-emerald-800';
          } else if (isActive) {
            badgeColor = 'bg-blue-50 border-blue-400 text-blue-800 animate-pulse';
          }

          return (
            <div
              key={s.id}
              className={`p-3 rounded-lg border text-left transition-all ${badgeColor}`}
            >
              <div className="flex items-center gap-2 mb-1">
                <div
                  className={`w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold ${
                    isDone
                      ? 'bg-emerald-600 text-white'
                      : isActive
                      ? 'bg-blue-600 text-white'
                      : 'bg-slate-300 text-slate-700'
                  }`}
                >
                  {isDone ? <Check className="w-3 h-3 stroke-[3]" /> : s.id}
                </div>
                <span className="text-xs font-semibold truncate">{s.name}</span>
              </div>
              <p className="text-[11px] text-slate-500 leading-snug line-clamp-1">
                {s.desc}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
};
