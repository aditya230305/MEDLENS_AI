import React from 'react';
import { AlertCircle } from 'lucide-react';

export const DisclaimerBanner: React.FC = () => {
  return (
    <div className="bg-amber-50 border-l-4 border-amber-500 p-3 sm:p-4 rounded-r-lg shadow-sm">
      <div className="flex items-start gap-3">
        <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
        <div className="text-xs sm:text-sm text-amber-800 leading-relaxed">
          <span className="font-semibold text-amber-900">Medical Informational Disclaimer:</span>{' '}
          MedLens AI is an academic educational and organizational tool designed to assist patients in understanding laboratory terminology and report structure. 
          It is <strong>not</strong> an automated diagnostic system and does <strong>not</strong> provide medical prescriptions or clinical treatment advice. 
          Always consult a licensed medical physician or healthcare provider for the interpretation of your medical findings.
        </div>
      </div>
    </div>
  );
};
