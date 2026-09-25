import React, { useEffect, useRef } from 'react';
import { ChatMessage } from '../types';
import { Bot, User, Wrench, Volume2 } from 'lucide-react';

interface LiveTranscriptProps {
  messages: ChatMessage[];
  interimTranscript: string;
  onPlayAudio?: (audioBase64: string) => void;
}

export const LiveTranscript: React.FC<LiveTranscriptProps> = ({
  messages,
  interimTranscript,
  onPlayAudio,
}) => {
  const scrollRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, interimTranscript]);

  const getToolDisplayName = (toolName: string) => {
    switch (toolName) {
      case 'save_person':
        return '💾 Saved contact to memory';
      case 'update_person':
        return '🔄 Updated contact details';
      case 'save_recommendation':
        return '💡 Recorded recommendation';
      case 'save_idea':
        return '✨ Captured new idea';
      case 'draft_followup':
      case 'create_followup':
        return '📝 Drafted follow-up action';
      case 'search_memory':
        return '🔍 Searched event memory';
      case 'find_people_by_topic':
        return '🎯 Found matching topic contacts';
      case 'find_related_people':
        return '🤝 Analyzed network connections';
      case 'generate_event_recap':
        return '📊 Generated event recap';
      default:
        return `⚡ Executed ${toolName}`;
    }
  };

  return (
    <div className="w-full flex flex-col h-full bg-[#111726]/80 rounded-2xl border border-slate-800/80 backdrop-blur-md overflow-hidden shadow-xl">
      <div className="px-4 py-2.5 border-b border-slate-800/80 bg-slate-900/40 flex items-center justify-between">
        <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-indigo-400 animate-pulse" />
          Live Transcript & Reasoning
        </span>
        <span className="text-[11px] text-slate-500 font-mono">Real-Time</span>
      </div>

      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-4 space-y-3.5 scrollbar-thin scrollbar-thumb-slate-700"
      >
        {messages.length === 0 && !interimTranscript && (
          <div className="h-full flex flex-col items-center justify-center text-center p-6 text-slate-500">
            <Bot className="w-8 h-8 mb-2 text-slate-600 opacity-60" />
            <p className="text-sm font-medium">No conversation yet</p>
            <p className="text-xs text-slate-600 mt-1 max-w-xs">
              Tap the orb or select a prompt below to start logging conversations or querying your event memory.
            </p>
          </div>
        )}

        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex flex-col ${
              msg.role === 'user' ? 'items-end' : 'items-start'
            }`}
          >
            <div
              className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-sm shadow-md transition-all ${
                msg.role === 'user'
                  ? 'bg-gradient-to-r from-indigo-600 to-indigo-700 text-white rounded-br-none'
                  : 'bg-slate-800/90 text-slate-100 rounded-bl-none border border-slate-700/60'
              }`}
            >
              <div className="flex items-center gap-2 mb-1">
                {msg.role === 'user' ? (
                  <span className="text-[10px] font-semibold uppercase tracking-wider text-indigo-200 flex items-center gap-1">
                    <User className="w-3 h-3" /> You
                  </span>
                ) : (
                  <span className="text-[10px] font-semibold uppercase tracking-wider text-emerald-300 flex items-center gap-1">
                    <Bot className="w-3 h-3" /> Wingman
                  </span>
                )}
                <span className="text-[10px] text-slate-400 ml-auto font-mono">
                  {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
              </div>

              {/* Message text */}
              <p className="leading-relaxed whitespace-pre-wrap">{msg.text}</p>

              {/* Tool Execution Pills */}
              {msg.toolCalls && msg.toolCalls.length > 0 && (
                <div className="mt-2.5 pt-2 border-t border-slate-700/50 flex flex-wrap gap-1.5">
                  {msg.toolCalls.map((tc, idx) => (
                    <span
                      key={idx}
                      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium bg-indigo-950/70 text-indigo-300 border border-indigo-700/40"
                    >
                      <Wrench className="w-2.5 h-2.5" />
                      {getToolDisplayName(tc.name)}
                    </span>
                  ))}
                </div>
              )}

              {/* Replay voice button */}
              {msg.audioBase64 && onPlayAudio && (
                <div className="mt-2 flex justify-end">
                  <button
                    onClick={() => onPlayAudio(msg.audioBase64!)}
                    className="text-[11px] text-pink-400 hover:text-pink-300 flex items-center gap-1 px-2 py-0.5 rounded bg-pink-950/40 border border-pink-800/40 hover:bg-pink-900/50 transition-colors"
                    title="Play voice response"
                  >
                    <Volume2 className="w-3 h-3" /> Listen
                  </button>
                </div>
              )}
            </div>
          </div>
        ))}

        {/* Live Interim Transcript (actively speaking) */}
        {interimTranscript && (
          <div className="flex flex-col items-end">
            <div className="max-w-[85%] rounded-2xl rounded-br-none px-4 py-2 text-sm bg-indigo-900/40 text-indigo-200 border border-indigo-500/40 animate-pulse">
              <span className="text-[10px] font-semibold uppercase tracking-wider text-indigo-300 block mb-0.5">
                Listening in real-time...
              </span>
              <p className="italic">{interimTranscript}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
