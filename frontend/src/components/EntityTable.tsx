import React, { useState } from 'react';
import { Search, AlertTriangle, CheckCircle, Pill, ClipboardList, Filter } from 'lucide-react';
import { StructuredMedicalRecord, TestStatus } from '../types';

interface EntityTableProps {
  record: StructuredMedicalRecord;
}

export const EntityTable: React.FC<EntityTableProps> = ({ record }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterAbnormal, setFilterAbnormal] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL');

  const categories = ['ALL', ...Array.from(new Set(record.tests.map(t => t.category)))];

  const filteredTests = record.tests.filter(t => {
    const matchesSearch = t.test_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          t.value.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesAbnormal = filterAbnormal ? (t.status !== 'NORMAL') : true;
    const matchesCategory = selectedCategory === 'ALL' || t.category === selectedCategory;
    return matchesSearch && matchesAbnormal && matchesCategory;
  });

  const getStatusBadge = (status: TestStatus) => {
    switch (status) {
      case 'HIGH':
      case 'CRITICAL_HIGH':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-rose-100 text-rose-800 border border-rose-200">
            <AlertTriangle className="w-3 h-3 text-rose-600" />
            HIGH
          </span>
        );
      case 'LOW':
      case 'CRITICAL_LOW':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-sky-100 text-sky-800 border border-sky-200">
            <AlertTriangle className="w-3 h-3 text-sky-600" />
            LOW
          </span>
        );
      case 'NORMAL':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 border border-emerald-200">
            <CheckCircle className="w-3 h-3 text-emerald-600" />
            NORMAL
          </span>
        );
      default:
        return (
          <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-700">
            {status}
          </span>
        );
    }
  };

  return (
    <div className="space-y-6">
      
      {/* Patient Demographics Card */}
      <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 sm:p-5 flex flex-wrap gap-4 sm:gap-8 items-center justify-between text-xs sm:text-sm">
        <div>
          <span className="text-slate-400 block text-[11px] font-semibold uppercase">Patient Name</span>
          <span className="font-bold text-slate-800">{record.patient_info.patient_name || 'Not specified in report'}</span>
        </div>
        <div>
          <span className="text-slate-400 block text-[11px] font-semibold uppercase">Age & Gender</span>
          <span className="font-bold text-slate-800">
            {record.patient_info.age || 'N/A'} {record.patient_info.gender ? `• ${record.patient_info.gender}` : ''}
          </span>
        </div>
        <div>
          <span className="text-slate-400 block text-[11px] font-semibold uppercase">Report Date</span>
          <span className="font-bold text-slate-800">{record.patient_info.report_date || 'N/A'}</span>
        </div>
        <div>
          <span className="text-slate-400 block text-[11px] font-semibold uppercase">Diagnostic Laboratory</span>
          <span className="font-bold text-slate-800">{record.patient_info.lab_name || 'Diagnostic Laboratory'}</span>
        </div>
        <div>
          <span className="text-slate-400 block text-[11px] font-semibold uppercase">Abnormal Parameters</span>
          <span className={`font-bold text-xs px-2.5 py-1 rounded-full ${record.abnormal_tests.length > 0 ? 'bg-rose-100 text-rose-800' : 'bg-emerald-100 text-emerald-800'}`}>
            {record.abnormal_tests.length} of {record.tests.length} flagged
          </span>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row gap-3 items-stretch sm:items-center justify-between">
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
          <input
            type="text"
            placeholder="Search lab test by name or value..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-4 py-2 rounded-lg border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white"
          />
        </div>

        <div className="flex items-center gap-2 overflow-x-auto pb-1">
          <button
            onClick={() => setFilterAbnormal(!filterAbnormal)}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors border ${
              filterAbnormal
                ? 'bg-rose-600 text-white border-rose-600'
                : 'bg-white text-slate-700 border-slate-300 hover:bg-slate-50'
            }`}
          >
            <AlertTriangle className="w-3.5 h-3.5" />
            <span>Abnormal Only ({record.abnormal_tests.length})</span>
          </button>

          {categories.length > 2 && (
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-white border border-slate-300 text-slate-700 focus:outline-none"
            >
              {categories.map((c) => (
                <option key={c} value={c}>
                  {c === 'ALL' ? 'All Panels' : c}
                </option>
              ))}
            </select>
          )}
        </div>
      </div>

      {/* Tests Table */}
      <div className="overflow-x-auto border border-slate-200 rounded-xl bg-white shadow-xs">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 text-xs font-semibold uppercase tracking-wider">
            <tr>
              <th className="py-3 px-4">Test / Parameter</th>
              <th className="py-3 px-4">Result Value</th>
              <th className="py-3 px-4">Units</th>
              <th className="py-3 px-4">Normal Reference Range</th>
              <th className="py-3 px-4">Status Flag</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 text-slate-800">
            {filteredTests.length === 0 ? (
              <tr>
                <td colSpan={5} className="py-8 text-center text-slate-400 text-sm">
                  No lab tests matched your search criteria.
                </td>
              </tr>
            ) : (
              filteredTests.map((test, idx) => {
                const isAbnormal = test.status !== 'NORMAL';
                return (
                  <tr
                    key={idx}
                    className={`hover:bg-slate-50 transition-colors ${
                      isAbnormal ? 'bg-rose-50/20' : ''
                    }`}
                  >
                    <td className="py-3.5 px-4 font-medium">
                      <div>
                        <span className="font-semibold text-slate-900">{test.test_name}</span>
                        <span className="block text-[11px] text-slate-400">{test.category}</span>
                      </div>
                    </td>
                    <td className="py-3.5 px-4 font-mono font-bold">
                      <span className={isAbnormal ? 'text-rose-600 font-extrabold text-base' : 'text-slate-800'}>
                        {test.value}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-slate-500 font-mono text-xs">
                      {test.unit || '—'}
                    </td>
                    <td className="py-3.5 px-4 text-slate-600 text-xs font-mono">
                      {test.reference_range || '—'}
                    </td>
                    <td className="py-3.5 px-4">
                      {getStatusBadge(test.status)}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Concurrent Medications or Clinical Findings (if detected) */}
      {(record.medications.length > 0 || record.findings.length > 0) && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {record.medications.length > 0 && (
            <div className="bg-white p-4 rounded-xl border border-slate-200">
              <div className="flex items-center gap-2 mb-3 text-slate-800 font-bold text-sm">
                <Pill className="w-4 h-4 text-blue-600" />
                <span>Detected Medications</span>
              </div>
              <ul className="space-y-2 text-xs text-slate-700">
                {record.medications.map((m, i) => (
                  <li key={i} className="flex justify-between items-center p-2 rounded bg-slate-50 border border-slate-100">
                    <span className="font-semibold text-slate-900">{m.name} {m.dosage ? `(${m.dosage})` : ''}</span>
                    <span className="text-slate-500">{m.purpose || 'Maintenance'}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {record.findings.length > 0 && (
            <div className="bg-white p-4 rounded-xl border border-slate-200">
              <div className="flex items-center gap-2 mb-3 text-slate-800 font-bold text-sm">
                <ClipboardList className="w-4 h-4 text-cyan-600" />
                <span>Clinical Impressions & Findings</span>
              </div>
              <ul className="space-y-2 text-xs text-slate-700">
                {record.findings.map((f, i) => (
                  <li key={i} className="p-2 rounded bg-slate-50 border border-slate-100">
                    <span className="font-medium text-slate-800">{f.observation}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

    </div>
  );
};
