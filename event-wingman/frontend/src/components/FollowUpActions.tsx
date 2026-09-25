import React, { useState } from 'react';
import { FollowUp } from '../types';
import { Check, X, RefreshCw, Edit3, ShieldAlert, CheckCircle2, Clock } from 'lucide-react';

interface FollowUpActionsProps {
  followups: FollowUp[];
  onApprove: (id: string) => void;
  onCancel: (id: string) => void;
  onEdit: (id: string, newMessage: string) => void;
  onRegenerate: (id: string, tone: string) => void;
}

export const FollowUpActions: React.FC<FollowUpActionsProps> = ({
  followups,
  onApprove,
  onCancel,
  onEdit,
  onRegenerate,
}) => {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editText, setEditText] = useState('');

  const startEditing = (fu: FollowUp) => {
    setEditingId(fu.id);
    setEditText(fu.draftMessage || '');
  };

  const saveEdit = (id: string) => {
    onEdit(id, editText);
    setEditingId(null);
  };

  return (
    <div className="w-full bg-[#111726]/80 rounded-2xl border border-slate-800/80 backdrop-blur-md overflow-hidden flex flex-col shadow-xl">
      {/* Header */}
      <div className="px-4 py-3 border-b border-slate-800/80 bg-slate-900/60 flex items-center justify-between">
        <div>
          <h2 className="text-sm font-semibold text-slate-200">Follow-Up Action Items</h2>
          <p className="text-[11px] text-slate-400">Contextual drafts ready for review & approval</p>
        </div>
        <span className="text-xs px-2.5 py-0.5 rounded-full bg-indigo-950 text-indigo-300 border border-indigo-800/50 font-mono">
          {followups.length} total
        </span>
      </div>

      {/* Strict Human-In-The-Loop Safety Notice */}
      <div className="px-4 py-2 bg-amber-950/30 border-b border-amber-900/30 flex items-center gap-2 text-xs text-amber-300/90 font-medium">
        <ShieldAlert className="w-4 h-4 text-amber-400 flex-shrink-0" />
        <span>Safety guarantee: Event Wingman NEVER sends emails or messages automatically.</span>
      </div>

      {/* Follow-up Cards List */}
      <div className="p-4 overflow-y-auto max-h-[460px] space-y-3.5">
        {followups.length === 0 ? (
          <div className="text-center py-10 text-slate-500">
            <Clock className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p className="text-sm">No follow-ups requested yet</p>
            <p className="text-xs text-slate-600 mt-1">Say "Draft a follow-up to Sarah" to generate a draft.</p>
          </div>
        ) : (
          followups.map((fu) => (
            <div
              key={fu.id}
              className={`p-4 rounded-xl border transition-all ${
                fu.status === 'approved'
                  ? 'bg-emerald-950/20 border-emerald-800/50'
                  : fu.status === 'cancelled'
                  ? 'bg-slate-900/40 border-slate-800/50 opacity-60'
                  : 'bg-slate-800/60 border-slate-700/60 hover:border-indigo-500/50'
              }`}
            >
              <div className="flex items-start justify-between gap-2 mb-2">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-slate-100 text-sm">
                      {fu.personName || 'Contact'}
                    </span>
                    {fu.personCompany && (
                      <span className="text-xs text-indigo-300 font-medium">
                        ({fu.personCompany})
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-slate-400 mt-0.5">{fu.action}</p>
                </div>

                {/* Status Badge */}
                <span
                  className={`text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full ${
                    fu.status === 'approved'
                      ? 'bg-emerald-950 text-emerald-300 border border-emerald-700/50'
                      : fu.status === 'cancelled'
                      ? 'bg-rose-950 text-rose-300 border border-rose-800/50'
                      : 'bg-amber-950 text-amber-300 border border-amber-800/50'
                  }`}
                >
                  {fu.status}
                </span>
              </div>

              {/* Draft Message Body */}
              {editingId === fu.id ? (
                <div className="space-y-2 mt-2">
                  <textarea
                    value={editText}
                    onChange={(e) => setEditText(e.target.value)}
                    rows={4}
                    className="w-full bg-slate-900 border border-indigo-500/60 rounded-lg p-2.5 text-xs text-slate-100 focus:outline-none focus:ring-1 focus:ring-indigo-400"
                  />
                  <div className="flex justify-end gap-2">
                    <button
                      onClick={() => setEditingId(null)}
                      className="px-2.5 py-1 text-xs rounded bg-slate-800 text-slate-300 hover:bg-slate-700"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={() => saveEdit(fu.id)}
                      className="px-2.5 py-1 text-xs rounded bg-indigo-600 text-white hover:bg-indigo-500"
                    >
                      Save Draft
                    </button>
                  </div>
                </div>
              ) : (
                <div className="bg-slate-900/70 p-3 rounded-lg border border-slate-800/80 mt-2 text-xs text-slate-300 leading-relaxed whitespace-pre-wrap font-sans">
                  {fu.draftMessage || '(Draft message pending generation)'}
                </div>
              )}

              {/* Action Buttons */}
              {fu.status === 'draft' && (
                <div className="flex flex-wrap items-center justify-between gap-2 mt-3 pt-2.5 border-t border-slate-700/40">
                  <div className="flex items-center gap-1.5">
                    <button
                      onClick={() => startEditing(fu)}
                      className="text-[11px] px-2.5 py-1 rounded bg-slate-800 text-slate-300 hover:bg-slate-700 hover:text-white transition-colors flex items-center gap-1"
                    >
                      <Edit3 className="w-3 h-3" /> Edit
                    </button>

                    <button
                      onClick={() => onRegenerate(fu.id, 'friendly_professional')}
                      className="text-[11px] px-2.5 py-1 rounded bg-slate-800 text-slate-300 hover:bg-slate-700 hover:text-white transition-colors flex items-center gap-1"
                    >
                      <RefreshCw className="w-3 h-3" /> Regenerate
                    </button>
                  </div>

                  <div className="flex items-center gap-1.5">
                    <button
                      onClick={() => onCancel(fu.id)}
                      className="text-[11px] px-2.5 py-1 rounded bg-rose-950/40 text-rose-300 hover:bg-rose-900/60 border border-rose-800/40 transition-colors flex items-center gap-1"
                    >
                      <X className="w-3 h-3" /> Dismiss
                    </button>

                    <button
                      onClick={() => onApprove(fu.id)}
                      className="text-[11px] font-semibold px-3 py-1 rounded bg-emerald-600 hover:bg-emerald-500 text-white transition-colors flex items-center gap-1 shadow-sm"
                    >
                      <Check className="w-3.5 h-3.5" /> Approve Draft
                    </button>
                  </div>
                </div>
              )}

              {fu.status === 'approved' && (
                <div className="mt-2 text-xs text-emerald-400 flex items-center gap-1 font-medium">
                  <CheckCircle2 className="w-3.5 h-3.5" /> Approved by you. Ready to copy and send in your email client.
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};
