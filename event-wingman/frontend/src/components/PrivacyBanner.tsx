import React, { useState } from 'react';
import { Shield, Trash2, Database, AlertTriangle, Eye } from 'lucide-react';

interface PrivacyBannerProps {
  isRecording: boolean;
  isDemoMode: boolean;
  onToggleDemoMode: () => void;
  onClearAll: () => void;
}

export const PrivacyBanner: React.FC<PrivacyBannerProps> = ({
  isRecording,
  isDemoMode,
  onToggleDemoMode,
  onClearAll,
}) => {
  const [showConfirm, setShowConfirm] = useState(false);

  const handleConfirmClear = () => {
    onClearAll();
    setShowConfirm(false);
  };

  return (
    <div className="w-full bg-slate-900/90 border border-slate-800 rounded-2xl p-3 flex flex-wrap items-center justify-between gap-3 text-xs text-slate-400">
      <div className="flex items-center gap-3">
        {/* Recording active badge */}
        <div className="flex items-center gap-1.5">
          <span
            className={`w-2.5 h-2.5 rounded-full ${
              isRecording ? 'bg-rose-500 animate-ping' : 'bg-slate-600'
            }`}
          />
          <span className={`font-semibold ${isRecording ? 'text-rose-400' : 'text-slate-400'}`}>
            {isRecording ? 'MIC LIVE (USER ACTIVE)' : 'MIC MUTED (SAFE)'}
          </span>
        </div>

        <span className="hidden sm:inline text-slate-600">|</span>

        {/* Local privacy guarantee */}
        <div className="hidden sm:flex items-center gap-1 text-slate-400">
          <Shield className="w-3.5 h-3.5 text-emerald-400" />
          <span>Local Temporary Event Store</span>
        </div>
      </div>

      <div className="flex items-center gap-2">
        {/* Demo Mode Toggle */}
        <button
          onClick={onToggleDemoMode}
          className={`px-3 py-1.5 rounded-xl font-medium transition-colors flex items-center gap-1.5 cursor-pointer ${
            isDemoMode
              ? 'bg-amber-950/80 text-amber-300 border border-amber-700/50'
              : 'bg-slate-800 text-slate-300 hover:bg-slate-700 border border-slate-700/60'
          }`}
          title="Toggle synthetic demo contacts (Sarah, Priya, Daniel)"
        >
          <Database className="w-3.5 h-3.5" />
          <span>{isDemoMode ? 'Demo Data: ON' : 'Load Demo Contacts'}</span>
        </button>

        {/* Clear Data with confirmation */}
        {showConfirm ? (
          <div className="flex items-center gap-1 bg-rose-950/80 p-1 rounded-xl border border-rose-800">
            <span className="text-[11px] text-rose-300 px-1">Clear all?</span>
            <button
              onClick={handleConfirmClear}
              className="px-2 py-0.5 rounded bg-rose-600 text-white font-bold text-[10px] hover:bg-rose-500"
            >
              Yes
            </button>
            <button
              onClick={() => setShowConfirm(false)}
              className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 text-[10px]"
            >
              No
            </button>
          </div>
        ) : (
          <button
            onClick={() => setShowConfirm(true)}
            className="p-1.5 rounded-xl text-slate-400 hover:text-rose-400 hover:bg-slate-800 transition-colors"
            title="Clear all stored event memories"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  );
};
