import React, { useRef } from 'react';
import { UploadCloud, FileText, Sparkles, CheckCircle2, ArrowRight } from 'lucide-react';

interface FileUploaderProps {
  onFileUpload: (file: File) => void;
  onSelectSample: (sampleFilename: string) => void;
  isProcessing: boolean;
  currentFilename?: string;
}

const SAMPLE_REPORTS = [
  {
    filename: 'Sample_Diabetic_Lipid_Panel.pdf',
    title: 'Diabetic & Lipid Panel',
    patient: 'Robert Miller (54M)',
    highlights: 'Elevated HbA1c (7.8%), High Cholesterol, High Triglycerides',
    tag: 'Metabolic & Cardiac Risk',
    badgeColor: 'bg-rose-100 text-rose-800 border-rose-200'
  },
  {
    filename: 'Sample_Anemia_CBC_Report.pdf',
    title: 'Anemia & CBC Report',
    patient: 'Emily Watson (28F)',
    highlights: 'Low Hemoglobin (9.2 g/dL), Low MCV (71.4 fL), High RDW',
    tag: 'Hematology & Microcytosis',
    badgeColor: 'bg-amber-100 text-amber-800 border-amber-200'
  },
  {
    filename: 'Sample_Comprehensive_Normal_Checkup.pdf',
    title: 'Normal Health Checkup',
    patient: 'David Miller (35M)',
    highlights: 'Normal CBC, Lipids, Renal, Liver & Thyroid (11 tests)',
    tag: 'Normal Baseline',
    badgeColor: 'bg-emerald-100 text-emerald-800 border-emerald-200'
  }
];

export const FileUploader: React.FC<FileUploaderProps> = ({
  onFileUpload,
  onSelectSample,
  isProcessing,
  currentFilename
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      onFileUpload(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      onFileUpload(e.target.files[0]);
    }
  };

  return (
    <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm mb-6">
      
      {/* Quick Demo Preloaded Reports for Examiner / Viva */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-blue-600" />
            <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider">
              Instant 1-Click Viva Demo Reports
            </h2>
          </div>
          <span className="text-xs text-slate-500">Click any report to analyze instantly</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {SAMPLE_REPORTS.map((s) => {
            const isSelected = currentFilename === s.filename;
            return (
              <button
                key={s.filename}
                onClick={() => onSelectSample(s.filename)}
                disabled={isProcessing}
                className={`p-4 rounded-xl border text-left transition-all relative overflow-hidden group ${
                  isSelected
                    ? 'border-blue-500 bg-blue-50/50 shadow-md ring-2 ring-blue-500/20'
                    : 'border-slate-200 hover:border-blue-300 hover:bg-slate-50'
                } ${isProcessing ? 'opacity-50 cursor-not-allowed' : ''}`}
              >
                <div className="flex items-start justify-between mb-2">
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${s.badgeColor}`}>
                    {s.tag}
                  </span>
                  {isSelected && (
                    <CheckCircle2 className="w-4 h-4 text-blue-600 flex-shrink-0" />
                  )}
                </div>
                <h3 className="text-sm font-bold text-slate-900 mb-1 group-hover:text-blue-600 transition-colors">
                  {s.title}
                </h3>
                <p className="text-xs text-slate-500 mb-2">Patient: {s.patient}</p>
                <p className="text-xs text-slate-600 line-clamp-2 leading-relaxed bg-slate-100/60 p-1.5 rounded-md">
                  {s.highlights}
                </p>
                <div className="mt-3 flex items-center gap-1 text-xs font-semibold text-blue-600 group-hover:translate-x-1 transition-transform">
                  <span>Analyze this report</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </div>
              </button>
            );
          })}
        </div>
      </div>

      <div className="relative my-4 flex items-center justify-center">
        <div className="border-t border-slate-200 w-full" />
        <span className="bg-white px-3 text-xs font-semibold text-slate-400 uppercase tracking-wider absolute">
          Or Upload Custom Medical Report
        </span>
      </div>

      {/* Drag & Drop Upload Zone */}
      <div
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors ${
          isProcessing
            ? 'border-slate-200 bg-slate-50 cursor-not-allowed'
            : 'border-slate-300 hover:border-blue-500 hover:bg-blue-50/20'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.png,.jpg,.jpeg,.tiff"
          onChange={handleFileChange}
          disabled={isProcessing}
          className="hidden"
        />

        <div className="w-12 h-12 mx-auto rounded-full bg-blue-50 text-blue-600 flex items-center justify-center mb-3">
          <UploadCloud className="w-6 h-6" />
        </div>

        <p className="text-sm font-semibold text-slate-800 mb-1">
          {isProcessing ? 'Processing report through multi-stage pipeline...' : 'Click or drag & drop medical report here'}
        </p>
        <p className="text-xs text-slate-500">
          Supports Digital PDFs, Scanned Image PDFs, PNG, JPG (Auto-detects OCR vs Digital Text)
        </p>

        {currentFilename && !isProcessing && (
          <div className="inline-flex items-center gap-1.5 mt-3 px-3 py-1 rounded-full bg-slate-100 text-slate-700 text-xs font-medium">
            <FileText className="w-3.5 h-3.5 text-blue-600" />
            <span>Active: {currentFilename}</span>
          </div>
        )}
      </div>

    </div>
  );
};
