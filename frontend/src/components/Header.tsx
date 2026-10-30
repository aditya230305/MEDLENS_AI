import React from 'react';
import { Activity, ShieldCheck, Cpu, BarChart2 } from 'lucide-react';
import { SystemHealthResponse } from '../types';

interface HeaderProps {
  health: SystemHealthResponse | null;
  onOpenEvaluation: () => void;
}

export const Header: React.FC<HeaderProps> = ({ health, onOpenEvaluation }) => {
  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        
        {/* Brand */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-cyan-500 flex items-center justify-center text-white shadow-md shadow-blue-500/20">
            <Activity className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold tracking-tight text-slate-900">MedLens AI</h1>
              <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-blue-100 text-blue-700">
                B.Tech Major Project
              </span>
            </div>
            <p className="text-xs text-slate-500 hidden sm:block">
              Intelligent Medical Report Analysis, Generation & Summarization
            </p>
          </div>
        </div>

        {/* Right Badges & Controls */}
        <div className="flex items-center gap-3">
          {/* LLM Status Badge */}
          <div className="hidden md:flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-slate-100 text-slate-700 border border-slate-200">
            <Cpu className="w-3.5 h-3.5 text-blue-600" />
            <span>LLM: {health?.gemini_configured ? (health?.gemini_model || 'Gemini 2.5 Flash') : 'Local Clinical Engine'}</span>
            <span className={`w-2 h-2 rounded-full ${health?.gemini_configured ? 'bg-emerald-500' : 'bg-amber-400'}`} />
          </div>

          {/* RAG Knowledge Base Badge */}
          <div className="hidden lg:flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-emerald-50 text-emerald-800 border border-emerald-200">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
            <span>RAG Active ({health?.knowledge_base_items || 13} Panels)</span>
          </div>

          {/* Viva Evaluation Button */}
          <button
            onClick={onOpenEvaluation}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs sm:text-sm font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 border border-slate-300 transition-colors shadow-2xs"
          >
            <BarChart2 className="w-4 h-4 text-blue-600" />
            <span>Viva Evaluation</span>
          </button>
        </div>

      </div>
    </header>
  );
};
