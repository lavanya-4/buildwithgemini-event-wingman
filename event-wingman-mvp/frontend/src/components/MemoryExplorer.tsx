import React, { useState } from 'react';
import { Person, Topic, Idea, Recommendation, Conversation } from '../types';
import { User, Tag, Sparkles, Lightbulb, Trash2, Building, MessageSquare, AlertCircle } from 'lucide-react';

interface MemoryExplorerProps {
  people: Person[];
  topics: Topic[];
  ideas: Idea[];
  recommendations: Recommendation[];
  conversations: Conversation[];
  onDeletePerson: (id: string) => void;
  onSelectPersonForRecall: (name: string) => void;
}

export const MemoryExplorer: React.FC<MemoryExplorerProps> = ({
  people,
  topics,
  ideas,
  recommendations,
  conversations,
  onDeletePerson,
  onSelectPersonForRecall,
}) => {
  const [activeTab, setActiveTab] = useState<'people' | 'topics' | 'recommendations' | 'ideas'>('people');

  return (
    <div className="w-full bg-[#111726]/80 rounded-2xl border border-slate-800/80 backdrop-blur-md overflow-hidden flex flex-col shadow-xl">
      {/* Tab Navigation */}
      <div className="flex border-b border-slate-800/80 bg-slate-900/60 p-1.5 gap-1">
        <button
          onClick={() => setActiveTab('people')}
          className={`flex-1 py-2 rounded-xl text-xs font-semibold flex items-center justify-center gap-1.5 transition-all cursor-pointer ${
            activeTab === 'people'
              ? 'bg-indigo-600 text-white shadow'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
          }`}
        >
          <User className="w-3.5 h-3.5" />
          People ({people.length})
        </button>

        <button
          onClick={() => setActiveTab('topics')}
          className={`flex-1 py-2 rounded-xl text-xs font-semibold flex items-center justify-center gap-1.5 transition-all cursor-pointer ${
            activeTab === 'topics'
              ? 'bg-indigo-600 text-white shadow'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
          }`}
        >
          <Tag className="w-3.5 h-3.5" />
          Topics ({topics.length})
        </button>

        <button
          onClick={() => setActiveTab('recommendations')}
          className={`flex-1 py-2 rounded-xl text-xs font-semibold flex items-center justify-center gap-1.5 transition-all cursor-pointer ${
            activeTab === 'recommendations'
              ? 'bg-indigo-600 text-white shadow'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
          }`}
        >
          <Lightbulb className="w-3.5 h-3.5" />
          Recs ({recommendations.length})
        </button>

        <button
          onClick={() => setActiveTab('ideas')}
          className={`flex-1 py-2 rounded-xl text-xs font-semibold flex items-center justify-center gap-1.5 transition-all cursor-pointer ${
            activeTab === 'ideas'
              ? 'bg-indigo-600 text-white shadow'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
          }`}
        >
          <Sparkles className="w-3.5 h-3.5" />
          Ideas ({ideas.length})
        </button>
      </div>

      {/* Content Area */}
      <div className="p-4 overflow-y-auto max-h-[460px] space-y-3">
        {/* PEOPLE TAB */}
        {activeTab === 'people' && (
          <>
            {people.length === 0 ? (
              <div className="text-center py-10 text-slate-500">
                <User className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">No contacts captured yet</p>
                <p className="text-xs text-slate-600 mt-1">Speak to Wingman to log people you meet.</p>
              </div>
            ) : (
              people.map((p) => (
                <div
                  key={p.id}
                  className="p-3.5 rounded-xl bg-slate-800/60 border border-slate-700/60 hover:border-indigo-500/50 transition-all flex flex-col gap-2 relative group"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-slate-100 text-sm">{p.name}</span>
                        {p.isDemo && (
                          <span className="text-[10px] px-1.5 py-0.2 rounded bg-amber-950/70 text-amber-400 border border-amber-800/50 font-mono">
                            DEMO
                          </span>
                        )}
                      </div>
                      {p.company && (
                        <div className="flex items-center gap-1 text-xs text-indigo-300 font-medium mt-0.5">
                          <Building className="w-3 h-3" />
                          <span>{p.company}</span>
                          {p.role && <span className="text-slate-400">• {p.role}</span>}
                        </div>
                      )}
                    </div>

                    <div className="flex items-center gap-1">
                      <button
                        onClick={() => onSelectPersonForRecall(p.name)}
                        className="text-xs px-2.5 py-1 rounded bg-indigo-900/40 text-indigo-300 hover:bg-indigo-800/60 transition-colors"
                      >
                        Ask
                      </button>
                      <button
                        onClick={() => onDeletePerson(p.id)}
                        className="p-1 rounded text-slate-400 hover:text-rose-400 hover:bg-rose-950/40 transition-colors"
                        title="Delete contact"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>

                  {/* Topics */}
                  {p.topics && p.topics.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-1">
                      {p.topics.map((t, idx) => (
                        <span
                          key={idx}
                          className="px-2 py-0.5 rounded-md text-[11px] bg-slate-900/80 text-emerald-300 border border-emerald-900/50"
                        >
                          {t}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))
            )}
          </>
        )}

        {/* TOPICS TAB */}
        {activeTab === 'topics' && (
          <>
            {topics.length === 0 ? (
              <div className="text-center py-10 text-slate-500">
                <Tag className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">No topics detected yet</p>
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-2">
                {topics.map((topic) => (
                  <div
                    key={topic.id}
                    className="p-3 rounded-xl bg-slate-800/60 border border-slate-700/60 flex items-center justify-between"
                  >
                    <span className="text-xs font-medium text-slate-200">{topic.name}</span>
                    <span className="text-[11px] px-2 py-0.5 rounded-full bg-emerald-950/80 text-emerald-300 border border-emerald-800/50 font-mono">
                      {topic.mentionCount}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </>
        )}

        {/* RECOMMENDATIONS TAB */}
        {activeTab === 'recommendations' && (
          <>
            {recommendations.length === 0 ? (
              <div className="text-center py-10 text-slate-500">
                <Lightbulb className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">No recommendations logged yet</p>
              </div>
            ) : (
              recommendations.map((rec) => (
                <div
                  key={rec.id}
                  className="p-3 rounded-xl bg-slate-800/60 border border-slate-700/60 flex flex-col gap-1"
                >
                  <p className="text-xs text-slate-200 font-medium">"{rec.content}"</p>
                  <div className="flex items-center gap-1 text-[11px] text-pink-400">
                    <span>💡 Recommendation</span>
                    {rec.context && <span className="text-slate-400">• {rec.context}</span>}
                  </div>
                </div>
              ))
            )}
          </>
        )}

        {/* IDEAS TAB */}
        {activeTab === 'ideas' && (
          <>
            {ideas.length === 0 ? (
              <div className="text-center py-10 text-slate-500">
                <Sparkles className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">No ideas saved yet</p>
              </div>
            ) : (
              ideas.map((idea) => (
                <div
                  key={idea.id}
                  className="p-3 rounded-xl bg-slate-800/60 border border-slate-700/60 flex flex-col gap-1"
                >
                  <h5 className="text-xs font-semibold text-amber-300">{idea.title}</h5>
                  {idea.description && (
                    <p className="text-xs text-slate-300">{idea.description}</p>
                  )}
                </div>
              ))
            )}
          </>
        )}
      </div>
    </div>
  );
};
