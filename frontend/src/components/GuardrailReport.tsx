import React from 'react';
import { ShieldCheck, AlertCircle, CheckCircle2, AlertTriangle, HelpCircle } from 'lucide-react';
import { ValidationReport } from '../types';

interface GuardrailReportProps {
  validation: ValidationReport;
}

export const GuardrailReport: React.FC<GuardrailReportProps> = ({ validation }) => {
  const score = validation.factual_consistency_score;
  const isHighQuality = score >= 85;

  return (
    <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-6">
      
      {/* Top Score Banner */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-5 rounded-xl bg-slate-50 border border-slate-200">
        <div className="flex items-center gap-4">
          <div className={`w-14 h-14 rounded-2xl flex items-center justify-center font-black text-xl shadow-sm ${
            isHighQuality
              ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
              : 'bg-amber-100 text-amber-800 border border-amber-300'
          }`}>
            {score.toFixed(0)}%
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-bold text-slate-900">
                Factual Consistency & Grounding Audit
              </h3>
              <span className={`text-[11px] font-bold px-2 py-0.5 rounded-full ${
                validation.is_valid ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'
              }`}>
                {validation.is_valid ? 'Audit Passed' : 'Discrepancy Flagged'}
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Cross-checked generated clinical claims against extracted report values & RAG knowledge base.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4 text-xs font-semibold text-slate-600 sm:border-l sm:border-slate-300 sm:pl-4">
          <div>
            <span className="text-slate-400 block text-[10px] uppercase font-bold">Verified Claims</span>
            <span className="text-sm font-bold text-emerald-600">{validation.verified_claims.length}</span>
          </div>
          <div>
            <span className="text-slate-400 block text-[10px] uppercase font-bold">Flagged Claims</span>
            <span className={`text-sm font-bold ${validation.flagged_claims.length > 0 ? 'text-rose-600' : 'text-slate-600'}`}>
              {validation.flagged_claims.length}
            </span>
          </div>
        </div>
      </div>

      {/* Flagged Claims Section (Hallucination Warning) */}
      {validation.flagged_claims.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center gap-2 text-rose-800 font-bold text-sm">
            <AlertTriangle className="w-4 h-4 text-rose-600" />
            <span>Flagged Statements / Potential Inconsistencies</span>
          </div>
          <div className="space-y-2">
            {validation.flagged_claims.map((claim, idx) => (
              <div key={idx} className="p-3.5 rounded-xl bg-rose-50/70 border border-rose-200 text-xs space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-rose-900 uppercase tracking-wider text-[10px]">
                    {claim.flag_type} ({claim.severity} Severity)
                  </span>
                </div>
                <p className="text-slate-800 font-mono text-[11px] bg-white p-2 rounded border border-rose-100">
                  "{claim.claim_text}"
                </p>
                <p className="text-rose-700 font-medium">
                  <strong>Guardrail Audit:</strong> {claim.explanation}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Verified Data Points Table */}
      <div className="space-y-3">
        <div className="flex items-center gap-2 text-slate-800 font-bold text-sm">
          <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          <span>Verified Entities Traceable to Report Source</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2.5">
          {validation.verified_claims.map((claim, idx) => (
            <div key={idx} className="p-3 rounded-lg bg-emerald-50/50 border border-emerald-100 flex items-start justify-between text-xs">
              <div>
                <span className="font-bold text-slate-900 block">{claim.entity}</span>
                <span className="font-mono text-emerald-700 font-semibold">{claim.reported_value}</span>
              </div>
              <ShieldCheck className="w-4 h-4 text-emerald-600 flex-shrink-0 mt-0.5" />
            </div>
          ))}
        </div>
      </div>

      {/* Audit Notes */}
      <div className="p-3 rounded-lg bg-slate-100/70 text-slate-600 text-xs">
        <strong>Audit Summary:</strong> {validation.audit_notes}
      </div>

    </div>
  );
};
