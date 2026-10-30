import React, { useState, useEffect } from 'react';
import { X, CheckCircle, XCircle, Star, Clock, ShieldCheck, BarChart2, RefreshCw } from 'lucide-react';
import { PipelineLatencies, AggregatedMetrics } from '../types';

interface EvaluationModalProps {
  isOpen: boolean;
  onClose: () => void;
  latencies?: PipelineLatencies;
  activeReportName?: string;
  guardrailScore?: number;
}

export const EvaluationModal: React.FC<EvaluationModalProps> = ({
  isOpen,
  onClose,
  latencies,
  activeReportName,
  guardrailScore
}) => {
  const [metrics, setMetrics] = useState<AggregatedMetrics | null>(null);
  const [rating, setRating] = useState<number>(5);
  const [isAccurate, setIsAccurate] = useState<boolean>(true);
  const [notes, setNotes] = useState<string>('');
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const fetchMetrics = async () => {
    try {
      const res = await fetch('/api/metrics');
      if (res.ok) {
        const data = await res.json();
        setMetrics(data);
      }
    } catch (err) {
      console.error('Failed to fetch metrics:', err);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchMetrics();
      setSubmitted(false);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleSubmitEvaluation = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);

    try {
      const res = await fetch('/api/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          report_name: activeReportName || 'Sample Report',
          is_accurate: isAccurate,
          accuracy_rating: rating,
          feedback_notes: notes,
          pipeline_latency_ms: latencies?.total_pipeline_ms || 0.0,
          guardrail_score: guardrailScore || 100.0
        })
      });

      if (res.ok) {
        const updated = await res.json();
        setMetrics(updated);
        setSubmitted(true);
      }
    } catch (err) {
      console.error('Failed to submit evaluation:', err);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-2xl border border-slate-200 p-6 space-y-6">
        
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div className="flex items-center gap-2">
            <BarChart2 className="w-5 h-5 text-blue-600" />
            <h2 className="text-lg font-bold text-slate-900">
              Viva Evaluation & Latency Dashboard
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Aggregate Project Statistics (for Viva presentation) */}
        <div>
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">
            Aggregate Project Performance Metrics
          </h3>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
            <div className="p-3 bg-blue-50 border border-blue-100 rounded-xl">
              <span className="text-[10px] font-semibold text-blue-600 uppercase block">Total Evaluations</span>
              <span className="text-xl font-black text-blue-950">{metrics?.total_evaluations || 0}</span>
            </div>
            <div className="p-3 bg-emerald-50 border border-emerald-100 rounded-xl">
              <span className="text-[10px] font-semibold text-emerald-600 uppercase block">Reliability Rate</span>
              <span className="text-xl font-black text-emerald-950">{metrics?.reliability_percentage || 100}%</span>
            </div>
            <div className="p-3 bg-indigo-50 border border-indigo-100 rounded-xl">
              <span className="text-[10px] font-semibold text-indigo-600 uppercase block">Avg Guardrail Score</span>
              <span className="text-xl font-black text-indigo-950">{metrics?.average_guardrail_score || 100}%</span>
            </div>
            <div className="p-3 bg-amber-50 border border-amber-100 rounded-xl">
              <span className="text-[10px] font-semibold text-amber-600 uppercase block">Avg Response Time</span>
              <span className="text-xl font-black text-amber-950">{(metrics?.average_latency_ms || 50).toFixed(0)} ms</span>
            </div>
          </div>
        </div>

        {/* Current Report Latency Breakdown */}
        {latencies && (
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3 flex items-center gap-1.5">
              <Clock className="w-3.5 h-3.5 text-blue-600" />
              <span>Current Run Stage Latencies ({latencies.total_pipeline_ms} ms total)</span>
            </h3>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5 text-xs">
              <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200">
                <span className="text-slate-500 block text-[10px]">1. Ingestion / PDF</span>
                <span className="font-bold text-slate-800">{latencies.ingestion_ms} ms</span>
              </div>
              <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200">
                <span className="text-slate-500 block text-[10px]">2. OCR Engine</span>
                <span className="font-bold text-slate-800">{latencies.ocr_ms} ms</span>
              </div>
              <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200">
                <span className="text-slate-500 block text-[10px]">3. Medical NLP</span>
                <span className="font-bold text-slate-800">{latencies.nlp_extraction_ms} ms</span>
              </div>
              <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200">
                <span className="text-slate-500 block text-[10px]">4. RAG Retrieval</span>
                <span className="font-bold text-slate-800">{latencies.rag_retrieval_ms} ms</span>
              </div>
              <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200">
                <span className="text-slate-500 block text-[10px]">5. LLM Summaries</span>
                <span className="font-bold text-slate-800">{latencies.llm_generation_ms} ms</span>
              </div>
              <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200">
                <span className="text-slate-500 block text-[10px]">6. Fact Guardrail</span>
                <span className="font-bold text-slate-800">{latencies.validation_ms} ms</span>
              </div>
            </div>
          </div>
        )}

        {/* Examiner Feedback Form */}
        <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
          <h3 className="text-sm font-bold text-slate-900 mb-2">
            Record Examiner Evaluation (Viva Defense Hook)
          </h3>
          <p className="text-xs text-slate-500 mb-4">
            Evaluate the clinical accuracy and readability of the current generated summary for: <strong>{activeReportName || 'Current Report'}</strong>.
          </p>

          {submitted ? (
            <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-emerald-800 text-xs font-semibold flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-emerald-600" />
              <span>Evaluation recorded and added to the project defense metrics!</span>
            </div>
          ) : (
            <form onSubmit={handleSubmitEvaluation} className="space-y-4">
              <div className="flex items-center gap-4">
                <button
                  type="button"
                  onClick={() => setIsAccurate(true)}
                  className={`flex-1 py-2 px-3 rounded-lg text-xs font-bold flex items-center justify-center gap-1.5 border transition-all ${
                    isAccurate
                      ? 'bg-emerald-600 text-white border-emerald-600 shadow-sm'
                      : 'bg-white text-slate-700 border-slate-300'
                  }`}
                >
                  <CheckCircle className="w-4 h-4" />
                  <span>Accurate (Reliable)</span>
                </button>
                <button
                  type="button"
                  onClick={() => setIsAccurate(false)}
                  className={`flex-1 py-2 px-3 rounded-lg text-xs font-bold flex items-center justify-center gap-1.5 border transition-all ${
                    !isAccurate
                      ? 'bg-rose-600 text-white border-rose-600 shadow-sm'
                      : 'bg-white text-slate-700 border-slate-300'
                  }`}
                >
                  <XCircle className="w-4 h-4" />
                  <span>Inaccurate (Contains Error)</span>
                </button>
              </div>

              {/* Star Rating */}
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-slate-700">Readability & Quality:</span>
                <div className="flex gap-1">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <button
                      key={star}
                      type="button"
                      onClick={() => setRating(star)}
                      className="p-1 text-amber-400 hover:scale-110 transition-transform"
                    >
                      <Star className={`w-5 h-5 ${star <= rating ? 'fill-amber-400' : 'text-slate-300'}`} />
                    </button>
                  ))}
                </div>
              </div>

              {/* Notes */}
              <input
                type="text"
                placeholder="Optional examiner / evaluator comment..."
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                className="w-full px-3 py-2 text-xs rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
              />

              <button
                type="submit"
                disabled={submitting}
                className="w-full py-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs rounded-lg transition-colors flex items-center justify-center gap-1.5"
              >
                {submitting ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <CheckCircle className="w-3.5 h-3.5" />}
                <span>Save Evaluation Mark</span>
              </button>
            </form>
          )}
        </div>

      </div>
    </div>
  );
};
