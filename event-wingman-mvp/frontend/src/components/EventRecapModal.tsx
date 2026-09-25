import React from 'react';
import { EventRecap } from '../types';
import { X, Trophy, Volume2, Sparkles, Lightbulb, Users, ArrowRight } from 'lucide-react';

interface EventRecapModalProps {
  recap: EventRecap | null;
  isOpen: boolean;
  onClose: () => void;
  onSpeakRecap: (script: string) => void;
}

export const EventRecapModal: React.FC<EventRecapModalProps> = ({
  recap,
  isOpen,
  onClose,
  onSpeakRecap,
}) => {
  if (!isOpen || !recap) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-200">
      <div className="relative w-full max-w-2xl bg-[#0F1423] border border-indigo-500/40 rounded-3xl p-6 shadow-2xl flex flex-col max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-2xl bg-indigo-600/30 border border-indigo-500/50 text-indigo-400">
              <Trophy className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-100">Event Recap & Intelligence</h2>
              <p className="text-xs text-slate-400">Your networking copilot's structured retrospective</p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Scrollable Content */}
        <div className="flex-1 overflow-y-auto py-5 space-y-6 pr-1">
          {/* Metrics Grid */}
          <div className="grid grid-cols-3 gap-3">
            <div className="p-3.5 rounded-2xl bg-slate-800/60 border border-slate-700/60 text-center">
              <span className="text-2xl font-extrabold text-indigo-400 block font-mono">
                {recap.metrics.peopleMet}
              </span>
              <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">
                People Met
              </span>
            </div>

            <div className="p-3.5 rounded-2xl bg-slate-800/60 border border-slate-700/60 text-center">
              <span className="text-2xl font-extrabold text-emerald-400 block font-mono">
                {recap.metrics.topics}
              </span>
              <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">
                Topics
              </span>
            </div>

            <div className="p-3.5 rounded-2xl bg-slate-800/60 border border-slate-700/60 text-center">
              <span className="text-2xl font-extrabold text-amber-400 block font-mono">
                {recap.metrics.ideasCaptured}
              </span>
              <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">
                Ideas Saved
              </span>
            </div>

            <div className="p-3.5 rounded-2xl bg-slate-800/60 border border-slate-700/60 text-center">
              <span className="text-2xl font-extrabold text-pink-400 block font-mono">
                {recap.metrics.followups}
              </span>
              <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">
                Follow-ups
              </span>
            </div>

            <div className="p-3.5 rounded-2xl bg-slate-800/60 border border-slate-700/60 text-center">
              <span className="text-2xl font-extrabold text-cyan-400 block font-mono">
                {recap.metrics.conversations}
              </span>
              <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">
                Discussions
              </span>
            </div>

            <div className="p-3.5 rounded-2xl bg-slate-800/60 border border-slate-700/60 text-center">
              <span className="text-2xl font-extrabold text-purple-400 block font-mono">
                {recap.metrics.potentialConnections}
              </span>
              <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">
                Matches
              </span>
            </div>
          </div>

          {/* Voice Summary Audio Card */}
          <div className="p-4 rounded-2xl bg-gradient-to-r from-indigo-950/60 to-purple-950/60 border border-indigo-700/40 flex items-center justify-between">
            <div className="space-y-1">
              <span className="text-xs font-semibold text-indigo-300 uppercase tracking-wider flex items-center gap-1.5">
                <Volume2 className="w-3.5 h-3.5" /> Spoken Retrospective
              </span>
              <p className="text-xs text-slate-300 italic max-w-md">"{recap.spokenScript}"</p>
            </div>
            <button
              onClick={() => onSpeakRecap(recap.spokenScript)}
              className="px-3 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center gap-1.5 shadow-lg shadow-indigo-600/30 transition-all cursor-pointer whitespace-nowrap"
            >
              <Volume2 className="w-4 h-4" /> Listen
            </button>
          </div>

          {/* Top Topics */}
          {recap.topTopics.length > 0 && (
            <div>
              <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2.5">
                Most Discussed Topics
              </h3>
              <div className="flex flex-wrap gap-2">
                {recap.topTopics.map((t) => (
                  <span
                    key={t.id}
                    className="px-3 py-1 rounded-xl text-xs font-medium bg-emerald-950/80 text-emerald-300 border border-emerald-800/50 flex items-center gap-1.5"
                  >
                    <span>{t.name}</span>
                    <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-emerald-900 font-mono">
                      {t.mentionCount}
                    </span>
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Actionable Recommendations */}
          {recap.recommendations.length > 0 && (
            <div>
              <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2.5 flex items-center gap-1">
                <Lightbulb className="w-3.5 h-3.5 text-pink-400" /> Key Recommendations
              </h3>
              <div className="space-y-2">
                {recap.recommendations.map((r) => (
                  <div
                    key={r.id}
                    className="p-3 rounded-xl bg-slate-800/50 border border-slate-700/50 text-xs text-slate-200"
                  >
                    "{r.content}"
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Potential Connections */}
          {recap.potentialConnections.length > 0 && (
            <div>
              <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2.5 flex items-center gap-1">
                <Users className="w-3.5 h-3.5 text-cyan-400" /> Potential Introductions
              </h3>
              <div className="space-y-2">
                {recap.potentialConnections.map((c, idx) => (
                  <div
                    key={idx}
                    className="p-3 rounded-xl bg-cyan-950/20 border border-cyan-800/40 text-xs text-slate-200"
                  >
                    <div className="font-semibold text-cyan-300 flex items-center gap-1.5 mb-1">
                      <span>{c.personA.name}</span>
                      <ArrowRight className="w-3 h-3 text-cyan-500" />
                      <span>{c.personB.name}</span>
                    </div>
                    <p className="text-slate-400">{c.explanation}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="pt-4 border-t border-slate-800 flex justify-end">
          <button
            onClick={onClose}
            className="px-5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold transition-colors"
          >
            Close Recap
          </button>
        </div>
      </div>
    </div>
  );
};
