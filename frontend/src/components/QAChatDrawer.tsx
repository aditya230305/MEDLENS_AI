import React, { useState } from 'react';
import { MessageSquare, X, Send, Bot, User, Sparkles, BookOpen, ChevronDown, ChevronUp } from 'lucide-react';
import { StructuredMedicalRecord, KnowledgeChunk } from '../types';

interface Message {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  citations?: KnowledgeChunk[];
}

interface QAChatDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  record: StructuredMedicalRecord | null;
}

export const QAChatDrawer: React.FC<QAChatDrawerProps> = ({ isOpen, onClose, record }) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      sender: 'assistant',
      text: "Hello! I am your MedLens Assistant. Ask me any questions about your uploaded lab results, normal ranges, or clinical terms, and I'll answer using grounded medical references."
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [expandedCitationId, setExpandedCitationId] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSend = async (questionText?: string) => {
    const q = (questionText || input).trim();
    if (!q || !record) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      sender: 'user',
      text: q
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const res = await fetch('/api/qa', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: q,
          record: record
        })
      });

      if (!res.ok) {
        throw new Error('Server returned error');
      }

      const data = await res.json();
      const botMsg: Message = {
        id: (Date.now() + 1).toString(),
        sender: 'assistant',
        text: data.answer,
        citations: data.retrieved_citations
      };
      setMessages((prev) => [...prev, botMsg]);
    } catch (err: any) {
      const errorMsg: Message = {
        id: (Date.now() + 1).toString(),
        sender: 'assistant',
        text: `Error processing question: ${err.message || 'Please check backend server'}`
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  // Quick suggestion chips based on report's abnormal parameters
  const getSuggestions = () => {
    if (!record || record.tests.length === 0) return [];
    const suggestions: string[] = [];

    if (record.abnormal_tests.length > 0) {
      const firstAb = record.abnormal_tests[0];
      suggestions.push(`Why is my ${firstAb.test_name} flagged ${firstAb.status}?`);
      suggestions.push('What dietary or lifestyle adjustments should I consider?');
      suggestions.push('What specific questions should I ask my doctor?');
    } else {
      suggestions.push('What does it mean that all my parameters are normal?');
      suggestions.push('When should I schedule my next routine checkup?');
    }

    return suggestions.slice(0, 3);
  };

  return (
    <div className="fixed inset-y-0 right-0 z-50 w-full sm:w-[460px] bg-white shadow-2xl border-l border-slate-200 flex flex-col transform transition-transform duration-300">
      
      {/* Drawer Header */}
      <div className="p-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-blue-600 text-white flex items-center justify-center">
            <Bot className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900">MedLens Q&A Assistant</h3>
            <span className="text-[11px] text-slate-500">RAG Grounded in your report</span>
          </div>
        </div>
        <button
          onClick={onClose}
          className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-200 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Suggestion Chips */}
      {getSuggestions().length > 0 && (
        <div className="p-3 bg-blue-50/50 border-b border-blue-100 flex flex-wrap gap-1.5">
          <span className="w-full text-[10px] font-bold uppercase tracking-wider text-blue-800 flex items-center gap-1 mb-1">
            <Sparkles className="w-3 h-3 text-blue-600" />
            Suggested Questions:
          </span>
          {getSuggestions().map((s, i) => (
            <button
              key={i}
              onClick={() => handleSend(s)}
              disabled={loading}
              className="text-xs text-left px-2.5 py-1 rounded-md bg-white border border-blue-200 text-blue-900 hover:bg-blue-100/60 transition-colors shadow-2xs"
            >
              {s}
            </button>
          ))}
        </div>
      )}

      {/* Messages Scroll Area */}
      <div className="flex-1 p-4 overflow-y-auto space-y-4">
        {messages.map((m) => (
          <div
            key={m.id}
            className={`flex gap-3 text-sm ${m.sender === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            {m.sender === 'assistant' && (
              <div className="w-7 h-7 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center flex-shrink-0 mt-0.5">
                <Bot className="w-4 h-4" />
              </div>
            )}

            <div className={`max-w-[85%] rounded-2xl p-3.5 space-y-2 ${
              m.sender === 'user'
                ? 'bg-blue-600 text-white rounded-br-none shadow-xs'
                : 'bg-slate-100 text-slate-800 rounded-bl-none border border-slate-200 shadow-2xs'
            }`}>
              <div className="whitespace-pre-wrap leading-relaxed text-xs sm:text-sm">
                {m.text}
              </div>

              {/* Citations section if present */}
              {m.citations && m.citations.length > 0 && (
                <div className="mt-2 pt-2 border-t border-slate-200 text-xs text-slate-600">
                  <div className="flex items-center gap-1 font-semibold text-[11px] text-slate-500 mb-1">
                    <BookOpen className="w-3 h-3 text-blue-600" />
                    <span>Grounding Citations ({m.citations.length})</span>
                  </div>
                  <div className="space-y-1">
                    {m.citations.map((c, cIdx) => (
                      <div key={cIdx} className="bg-white p-2 rounded border border-slate-200 text-[11px]">
                        <div
                          onClick={() => setExpandedCitationId(expandedCitationId === c.chunk_id ? null : c.chunk_id)}
                          className="flex items-center justify-between font-bold text-blue-950 cursor-pointer"
                        >
                          <span>{c.title}</span>
                          {expandedCitationId === c.chunk_id ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                        </div>
                        {expandedCitationId === c.chunk_id && (
                          <p className="mt-1 text-slate-600 whitespace-pre-wrap border-t border-slate-100 pt-1">
                            {c.content}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {m.sender === 'user' && (
              <div className="w-7 h-7 rounded-full bg-slate-200 text-slate-600 flex items-center justify-center flex-shrink-0 mt-0.5">
                <User className="w-4 h-4" />
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="flex gap-2 items-center text-xs text-slate-400 italic">
            <Bot className="w-4 h-4 text-blue-600 animate-spin" />
            <span>Consulting medical knowledge base...</span>
          </div>
        )}
      </div>

      {/* Input Form */}
      <div className="p-3 border-t border-slate-200 bg-white">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex items-center gap-2"
        >
          <input
            type="text"
            placeholder={record ? "Ask a follow-up question..." : "Upload a report first"}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={loading || !record}
            className="flex-1 px-3 py-2 text-sm rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-slate-100"
          />
          <button
            type="submit"
            disabled={loading || !input.trim() || !record}
            className="p-2 rounded-xl bg-blue-600 text-white hover:bg-blue-700 disabled:bg-slate-300 disabled:cursor-not-allowed transition-colors"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>

    </div>
  );
};
