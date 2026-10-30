import React, { useState, useEffect } from 'react';
import { 
  FileText, 
  Stethoscope, 
  HeartHandshake, 
  Table, 
  ShieldCheck, 
  MessageSquare, 
  BarChart2, 
  Sparkles,
  AlertCircle
} from 'lucide-react';

import { Header } from './components/Header';
import { DisclaimerBanner } from './components/DisclaimerBanner';
import { FileUploader } from './components/FileUploader';
import { PipelineStepper } from './components/PipelineStepper';
import { EntityTable } from './components/EntityTable';
import { StructuredSummary } from './components/StructuredSummary';
import { PatientExplanation } from './components/PatientExplanation';
import { GuardrailReport } from './components/GuardrailReport';
import { QAChatDrawer } from './components/QAChatDrawer';
import { EvaluationModal } from './components/EvaluationModal';

import { 
  ProcessReportResponse, 
  SystemHealthResponse 
} from './types';

type ActiveTab = 'summary' | 'explanation' | 'entities' | 'guardrail';

export const App: React.FC = () => {
  const [health, setHealth] = useState<SystemHealthResponse | null>(null);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [currentStage, setCurrentStage] = useState<number>(0);
  const [reportData, setReportData] = useState<ProcessReportResponse | null>(null);
  const [activeTab, setActiveTab] = useState<ActiveTab>('summary');
  const [isQADrawerOpen, setIsQADrawerOpen] = useState<boolean>(false);
  const [isEvaluationOpen, setIsEvaluationOpen] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Load system health on mount
  useEffect(() => {
    fetchHealth();
    // Auto-load first sample report on load for instant demo
    handleSelectSample('Sample_Diabetic_Lipid_Panel.pdf');
  }, []);

  const fetchHealth = async () => {
    try {
      const res = await fetch('/api/health');
      if (res.ok) {
        const data = await res.json();
        setHealth(data);
      }
    } catch (err) {
      console.warn('Backend not yet reachable on /api/health');
    }
  };

  const simulatePipelineStages = async () => {
    setIsProcessing(true);
    setErrorMsg(null);
    setCurrentStage(1);
    await new Promise((r) => setTimeout(r, 150));
    setCurrentStage(2);
    await new Promise((r) => setTimeout(r, 150));
    setCurrentStage(3);
    await new Promise((r) => setTimeout(r, 150));
    setCurrentStage(4);
    await new Promise((r) => setTimeout(r, 150));
    setCurrentStage(5);
    await new Promise((r) => setTimeout(r, 200));
    setCurrentStage(6);
  };

  const handleSelectSample = async (sampleFilename: string) => {
    try {
      simulatePipelineStages();
      const res = await fetch(`/api/process-sample/${sampleFilename}`, {
        method: 'POST'
      });

      if (!res.ok) {
        throw new Error(`Failed to process sample report: ${res.statusText}`);
      }

      const data: ProcessReportResponse = await res.json();
      setReportData(data);
      setCurrentStage(7); // Completed
    } catch (err: any) {
      setErrorMsg(err.message || 'Error processing sample report');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleFileUpload = async (file: File) => {
    try {
      simulatePipelineStages();
      const formData = new FormData();
      formData.append('file', file);

      const res = await fetch('/api/process-upload', {
        method: 'POST',
        body: formData
      });

      if (!res.ok) {
        throw new Error(`Upload processing failed: ${res.statusText}`);
      }

      const data: ProcessReportResponse = await res.json();
      setReportData(data);
      setCurrentStage(7);
    } catch (err: any) {
      setErrorMsg(err.message || 'Error processing uploaded file');
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 text-slate-900 pb-16">
      
      {/* Navigation Header */}
      <Header 
        health={health} 
        onOpenEvaluation={() => setIsEvaluationOpen(true)} 
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        
        {/* Mandatory Medical Disclaimer Banner */}
        <DisclaimerBanner />

        {/* File Ingestion & Sample Picker */}
        <FileUploader
          onFileUpload={handleFileUpload}
          onSelectSample={handleSelectSample}
          isProcessing={isProcessing}
          currentFilename={reportData?.file_name}
        />

        {/* Live Modular Pipeline Stepper */}
        <PipelineStepper
          currentStage={currentStage}
          latencies={reportData?.latencies}
          isProcessing={isProcessing}
        />

        {/* Error Alert */}
        {errorMsg && (
          <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-sm flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-rose-600 flex-shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Report Results Dashboard */}
        {reportData && (
          <div className="space-y-4">
            
            {/* Tab Navigation Header & Interactive Q&A Trigger */}
            <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 border-b border-slate-200 pb-2">
              
              <div className="flex items-center gap-2 overflow-x-auto pb-1">
                <button
                  onClick={() => setActiveTab('summary')}
                  className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs sm:text-sm font-bold transition-all ${
                    activeTab === 'summary'
                      ? 'bg-blue-600 text-white shadow-sm'
                      : 'bg-white text-slate-700 hover:bg-slate-100 border border-slate-200'
                  }`}
                >
                  <Stethoscope className="w-4 h-4" />
                  <span>Structured Summary</span>
                </button>

                <button
                  onClick={() => setActiveTab('explanation')}
                  className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs sm:text-sm font-bold transition-all ${
                    activeTab === 'explanation'
                      ? 'bg-emerald-600 text-white shadow-sm'
                      : 'bg-white text-slate-700 hover:bg-slate-100 border border-slate-200'
                  }`}
                >
                  <HeartHandshake className="w-4 h-4" />
                  <span>Patient Plain Guide</span>
                </button>

                <button
                  onClick={() => setActiveTab('entities')}
                  className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs sm:text-sm font-bold transition-all ${
                    activeTab === 'entities'
                      ? 'bg-indigo-600 text-white shadow-sm'
                      : 'bg-white text-slate-700 hover:bg-slate-100 border border-slate-200'
                  }`}
                >
                  <Table className="w-4 h-4" />
                  <span>Extracted Entities ({reportData.record.tests.length})</span>
                </button>

                <button
                  onClick={() => setActiveTab('guardrail')}
                  className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs sm:text-sm font-bold transition-all ${
                    activeTab === 'guardrail'
                      ? 'bg-amber-600 text-white shadow-sm'
                      : 'bg-white text-slate-700 hover:bg-slate-100 border border-slate-200'
                  }`}
                >
                  <ShieldCheck className="w-4 h-4" />
                  <span>Fact Guardrail ({reportData.validation.factual_consistency_score.toFixed(0)}%)</span>
                </button>
              </div>

              {/* Ask Question Floating Action Button */}
              <button
                onClick={() => setIsQADrawerOpen(true)}
                className="flex items-center justify-center gap-2 px-4 py-2 rounded-xl text-xs sm:text-sm font-bold bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white shadow-md shadow-blue-500/20 transition-all hover:scale-[1.02]"
              >
                <MessageSquare className="w-4 h-4" />
                <span>Ask Q&A About Report</span>
              </button>
            </div>

            {/* Tab Views */}
            <div className="pt-2">
              {activeTab === 'summary' && (
                <StructuredSummary summaryText={reportData.structured_summary} />
              )}

              {activeTab === 'explanation' && (
                <PatientExplanation explanationText={reportData.patient_explanation} />
              )}

              {activeTab === 'entities' && (
                <EntityTable record={reportData.record} />
              )}

              {activeTab === 'guardrail' && (
                <GuardrailReport validation={reportData.validation} />
              )}
            </div>

          </div>
        )}

      </main>

      {/* Interactive RAG Q&A Drawer */}
      <QAChatDrawer
        isOpen={isQADrawerOpen}
        onClose={() => setIsQADrawerOpen(false)}
        record={reportData ? reportData.record : null}
      />

      {/* Viva Evaluation & Latency Modal */}
      <EvaluationModal
        isOpen={isEvaluationOpen}
        onClose={() => setIsEvaluationOpen(false)}
        latencies={reportData?.latencies}
        activeReportName={reportData?.file_name}
        guardrailScore={reportData?.validation?.factual_consistency_score}
      />

    </div>
  );
};

export default App;
