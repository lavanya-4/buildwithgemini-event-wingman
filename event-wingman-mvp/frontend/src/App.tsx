import React, { useEffect, useRef, useState, useCallback } from 'react';
import { AgentState, ChatMessage, Person } from './types';
import * as api from './services/api';
import { Mic, MicOff, Send, Volume2, RotateCcw, User, Loader2 } from 'lucide-react';

export const App: React.FC = () => {
  // Agent & Audio states
  const [agentState, setAgentState] = useState<AgentState>('IDLE');
  const [isRecording, setIsRecording] = useState<boolean>(false);
  const [interimTranscript, setInterimTranscript] = useState<string>('');
  const [textInput, setTextInput] = useState<string>('');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [people, setPeople] = useState<Person[]>([]);
  const [statusMessage, setStatusMessage] = useState<string>('');

  // Audio & Recorder references
  const currentAudioRef = useRef<HTMLAudioElement | null>(null);
  const recognitionRef = useRef<any>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const micStreamRef = useRef<MediaStream | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  // Auto scroll messages to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, interimTranscript]);

  // Load recent people
  const loadPeople = useCallback(async () => {
    try {
      const data = await api.fetchPeople();
      setPeople(data || []);
    } catch (err) {
      console.error('Failed to load people:', err);
    }
  }, []);

  useEffect(() => {
    loadPeople();
  }, [loadPeople]);

  // Interruption / Barge-in
  const handleInterrupt = useCallback(() => {
    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
      currentAudioRef.current = null;
    }
    if ('speechSynthesis' in window && window.speechSynthesis.speaking) {
      window.speechSynthesis.cancel();
    }
    if (agentState === 'SPEAKING') {
      setAgentState('IDLE');
    }
  }, [agentState]);

  // Play audio response (via backend audio or browser Web Speech synthesis)
  const playResponseAudio = useCallback((text: string, audioBase64?: string) => {
    handleInterrupt();

    if (audioBase64) {
      try {
        const audio = new Audio(`data:audio/mp3;base64,${audioBase64}`);
        currentAudioRef.current = audio;
        setAgentState('SPEAKING');

        audio.onended = () => {
          currentAudioRef.current = null;
          setAgentState('IDLE');
        };

        audio.onerror = () => {
          currentAudioRef.current = null;
          fallbackSpeechSynthesis(text);
        };

        audio.play().catch(() => {
          fallbackSpeechSynthesis(text);
        });
        return;
      } catch {
        fallbackSpeechSynthesis(text);
        return;
      }
    }

    fallbackSpeechSynthesis(text);
  }, [handleInterrupt]);

  const fallbackSpeechSynthesis = (text: string) => {
    if ('speechSynthesis' in window && text) {
      try {
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 1.0;
        utterance.pitch = 1.0;
        setAgentState('SPEAKING');
        utterance.onend = () => setAgentState('IDLE');
        utterance.onerror = () => setAgentState('IDLE');
        window.speechSynthesis.speak(utterance);
      } catch {
        setAgentState('IDLE');
      }
    } else {
      setAgentState('IDLE');
    }
  };

  // Process text message through Gemini
  const handleSendMessage = async (text: string) => {
    const cleanText = text.trim();
    if (!cleanText) return;

    handleInterrupt();

    const userMsg: ChatMessage = {
      id: `user_${Date.now()}`,
      role: 'user',
      text: cleanText,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setTextInput('');
    setInterimTranscript('');
    setAgentState('THINKING');
    setStatusMessage('Gemini is thinking...');

    try {
      const result = await api.sendChatMessage(cleanText, true);
      const responseText = result.responseText || "I've processed that.";

      const agentMsg: ChatMessage = {
        id: `agent_${Date.now()}`,
        role: 'agent',
        text: responseText,
        timestamp: new Date().toISOString(),
        toolCalls: result.toolCalls,
        audioBase64: result.audioBase64,
      };

      setMessages((prev) => [...prev, agentMsg]);
      setStatusMessage('');

      // Play audio reply
      playResponseAudio(responseText, result.audioBase64);

      // Refresh recent people in memory
      await loadPeople();
    } catch (err: any) {
      console.error('Chat error:', err);
      const errorMsg: ChatMessage = {
        id: `sys_${Date.now()}`,
        role: 'system',
        text: `Error: ${err.message || 'Could not communicate with Gemini'}`,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMsg]);
      setAgentState('IDLE');
      setStatusMessage('');
    }
  };

  // Start voice recording & speech recognition
  const startListening = async () => {
    handleInterrupt();
    audioChunksRef.current = [];

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      micStreamRef.current = stream;

      // 1. Setup MediaRecorder for robust audio capture
      try {
        const mediaRecorder = new MediaRecorder(stream);
        audioChunksRef.current = [];
        mediaRecorder.ondataavailable = (e) => {
          if (e.data && e.data.size > 0) {
            audioChunksRef.current.push(e.data);
          }
        };
        mediaRecorder.start(250);
        mediaRecorderRef.current = mediaRecorder;
      } catch (recErr) {
        console.warn('MediaRecorder init warning:', recErr);
      }

      // 2. Setup Web Speech API if supported
      const SpeechRecognition =
        (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

      if (SpeechRecognition) {
        const recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = true;
        recognition.lang = 'en-US';

        let speechCaptured = false;

        recognition.onstart = () => {
          setIsRecording(true);
          setAgentState('LISTENING');
          setStatusMessage('Listening to your voice...');
        };

        recognition.onresult = (event: any) => {
          let interim = '';
          let final = '';

          for (let i = event.resultIndex; i < event.results.length; i++) {
            const transcript = event.results[i][0].transcript;
            if (event.results[i].isFinal) {
              final += transcript;
            } else {
              interim += transcript;
            }
          }

          if (interim) setInterimTranscript(interim);

          if (final.trim()) {
            speechCaptured = true;
            stopListening();
            handleSendMessage(final.trim());
          }
        };

        recognition.onerror = (event: any) => {
          console.warn('SpeechRecognition error:', event.error);
        };

        recognition.onend = () => {
          if (isRecording && !speechCaptured) {
            stopListening();
          }
        };

        recognition.start();
        recognitionRef.current = recognition;
      } else {
        setIsRecording(true);
        setAgentState('LISTENING');
        setStatusMessage('Recording audio (click Stop when finished)...');
      }
    } catch (err) {
      console.error('Microphone error:', err);
      alert('Microphone access could not be established. You can type in the box below.');
      setIsRecording(false);
      setAgentState('IDLE');
    }
  };

  // Stop voice recording and process audio if needed
  const stopListening = async () => {
    setIsRecording(false);
    setStatusMessage('');

    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch {}
      recognitionRef.current = null;
    }

    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
      // If Web Speech did not send a message and audio was recorded, send to backend
      setTimeout(async () => {
        if (audioChunksRef.current.length > 0 && !interimTranscript) {
          const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
          if (audioBlob.size > 2000) {
            setAgentState('THINKING');
            setStatusMessage('Transcribing speech...');
            try {
              const res = await api.processAudioFile(audioBlob);
              if (res.transcript) {
                const userMsg: ChatMessage = {
                  id: `user_${Date.now()}`,
                  role: 'user',
                  text: res.transcript,
                  timestamp: new Date().toISOString(),
                };
                setMessages((prev) => [...prev, userMsg]);
                const agentMsg: ChatMessage = {
                  id: `agent_${Date.now()}`,
                  role: 'agent',
                  text: res.responseText,
                  timestamp: new Date().toISOString(),
                  audioBase64: res.audioBase64,
                };
                setMessages((prev) => [...prev, agentMsg]);
                playResponseAudio(res.responseText, res.audioBase64);
                loadPeople();
              }
            } catch (procErr) {
              console.warn('Audio processing fallback failed:', procErr);
            } finally {
              setStatusMessage('');
              setAgentState('IDLE');
            }
          }
        }
      }, 300);
    }

    if (micStreamRef.current) {
      micStreamRef.current.getTracks().forEach((track) => track.stop());
      micStreamRef.current = null;
    }

    setInterimTranscript('');
    if (agentState === 'LISTENING') {
      setAgentState('IDLE');
    }
  };

  const toggleMic = () => {
    if (isRecording) {
      stopListening();
    } else {
      startListening();
    }
  };

  const handleClearMemory = async () => {
    if (window.confirm('Clear all stored event memories?')) {
      handleInterrupt();
      await api.clearAllMemories();
      setMessages([]);
      setPeople([]);
    }
  };

  return (
    <div className="min-h-screen bg-[#0d1117] text-slate-100 flex flex-col items-center p-4 md:p-8 font-sans">
      <div className="w-full max-w-4xl flex flex-col gap-6">
        
        {/* Header */}
        <header className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
              EventWingman Voice Agent
            </h1>
            <p className="text-xs text-slate-400 mt-0.5">
              Natural voice copilot for saving & recalling event connections
            </p>
          </div>

          <button
            onClick={handleClearMemory}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-slate-400 hover:text-red-400 hover:bg-slate-800/80 transition cursor-pointer"
            title="Clear all stored memory"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reset Memory</span>
          </button>
        </header>

        {/* Core Voice Action */}
        <section className="flex flex-col items-center justify-center p-6 bg-slate-900/70 border border-slate-800 rounded-2xl shadow-xl gap-4">
          <div className="flex flex-col items-center gap-3">
            <button
              onClick={toggleMic}
              aria-label="Toggle Microphone"
              className={`relative w-20 h-20 rounded-full flex items-center justify-center transition-all duration-300 shadow-lg cursor-pointer ${
                isRecording
                  ? 'bg-red-500 hover:bg-red-600 text-white shadow-red-500/50 scale-105 animate-pulse'
                  : agentState === 'SPEAKING'
                  ? 'bg-amber-500 hover:bg-amber-600 text-white shadow-amber-500/40 animate-pulse'
                  : agentState === 'THINKING'
                  ? 'bg-indigo-600 text-white'
                  : 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-indigo-600/40 hover:scale-105'
              }`}
            >
              {agentState === 'THINKING' ? (
                <Loader2 className="w-9 h-9 animate-spin" />
              ) : isRecording ? (
                <MicOff className="w-9 h-9" />
              ) : agentState === 'SPEAKING' ? (
                <Volume2 className="w-9 h-9" />
              ) : (
                <Mic className="w-9 h-9" />
              )}
            </button>

            {/* State & Instructions */}
            <div className="text-center">
              <span className="text-sm font-semibold text-slate-200">
                {isRecording
                  ? 'Listening... Click to Stop'
                  : agentState === 'THINKING'
                  ? 'Gemini is thinking...'
                  : agentState === 'SPEAKING'
                  ? 'Gemini is speaking (Click to Interrupt)'
                  : '[ Voice / Microphone ] — Click to Speak'}
              </span>
              {statusMessage && (
                <p className="text-xs text-indigo-400 mt-1 animate-pulse">{statusMessage}</p>
              )}
              {interimTranscript && (
                <p className="text-xs text-slate-300 italic mt-1 bg-slate-800/80 px-3 py-1 rounded-full">
                  "{interimTranscript}"
                </p>
              )}
            </div>
          </div>

          {/* Text Input Fallback */}
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage(textInput);
            }}
            className="w-full max-w-xl flex items-center gap-2 mt-2"
          >
            <input
              type="text"
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
              placeholder="Or type here (e.g. 'I met Sarah from Google...', 'Who did I meet?')..."
              className="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-4 py-2 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition"
              disabled={agentState === 'THINKING'}
            />
            <button
              type="submit"
              disabled={!textInput.trim() || agentState === 'THINKING'}
              className="p-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 disabled:text-slate-600 text-white rounded-xl transition cursor-pointer"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>

          {/* Quick Click Prompts */}
          <div className="flex flex-wrap items-center justify-center gap-2 pt-1">
            <span className="text-[11px] text-slate-500">Quick Test:</span>
            <button
              onClick={() =>
                handleSendMessage(
                  'I met Sarah from Google. She works on voice AI and recommended Gemini Live.'
                )
              }
              className="text-[11px] px-2.5 py-1 rounded-md bg-slate-800/60 hover:bg-slate-800 text-slate-300 border border-slate-700/50 transition cursor-pointer"
            >
              "I met Sarah from Google..."
            </button>
            <button
              onClick={() => handleSendMessage('Who did I meet from Google?')}
              className="text-[11px] px-2.5 py-1 rounded-md bg-slate-800/60 hover:bg-slate-800 text-slate-300 border border-slate-700/50 transition cursor-pointer"
            >
              "Who did I meet from Google?"
            </button>
            <button
              onClick={() => handleSendMessage('What did Sarah recommend?')}
              className="text-[11px] px-2.5 py-1 rounded-md bg-slate-800/60 hover:bg-slate-800 text-slate-300 border border-slate-700/50 transition cursor-pointer"
            >
              "What did Sarah recommend?"
            </button>
            <button
              onClick={() => handleSendMessage('Who did I talk to about voice AI?')}
              className="text-[11px] px-2.5 py-1 rounded-md bg-slate-800/60 hover:bg-slate-800 text-slate-300 border border-slate-700/50 transition cursor-pointer"
            >
              "Who did I talk to about voice AI?"
            </button>
          </div>
        </section>

        {/* Content Grid: Live Conversation & Recent People */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
          
          {/* Live Conversation */}
          <section className="md:col-span-7 flex flex-col bg-slate-900/50 border border-slate-800 rounded-2xl p-4 min-h-[350px] max-h-[500px]">
            <h2 className="text-sm font-semibold text-slate-200 pb-3 border-b border-slate-800/80 flex items-center justify-between">
              <span>Live conversation</span>
              <span className="text-[11px] font-normal text-slate-400">
                {messages.length} message{messages.length === 1 ? '' : 's'}
              </span>
            </h2>

            <div className="flex-1 overflow-y-auto space-y-3 py-3 pr-1">
              {messages.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-center text-slate-500 py-10 px-4">
                  <Mic className="w-8 h-8 mb-2 opacity-30 text-indigo-400" />
                  <p className="text-xs">Speak into the microphone or use the quick buttons above.</p>
                  <p className="text-[11px] text-slate-600 mt-1">
                    Try introducing someone: "I met Sarah from Google..."
                  </p>
                </div>
              ) : (
                messages.map((m) => (
                  <div
                    key={m.id}
                    className={`flex flex-col ${m.role === 'user' ? 'items-end' : 'items-start'}`}
                  >
                    <div className="flex items-center gap-1.5 mb-1 px-1">
                      <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
                        {m.role === 'user' ? 'You' : 'Gemini'}
                      </span>
                    </div>

                    <div
                      className={`max-w-[88%] rounded-2xl px-4 py-2.5 text-xs leading-relaxed shadow-sm ${
                        m.role === 'user'
                          ? 'bg-indigo-600 text-white rounded-tr-sm'
                          : m.role === 'system'
                          ? 'bg-red-950/60 text-red-200 border border-red-900/60'
                          : 'bg-slate-800 text-slate-200 rounded-tl-sm border border-slate-700/60'
                      }`}
                    >
                      <p>{m.text}</p>

                      {m.role === 'agent' && (
                        <div className="mt-2 pt-2 border-t border-slate-700/40 flex items-center justify-between">
                          <button
                            onClick={() => playResponseAudio(m.text, m.audioBase64)}
                            className="text-[10px] text-indigo-400 hover:text-indigo-300 flex items-center gap-1 cursor-pointer"
                          >
                            <Volume2 className="w-3 h-3" />
                            <span>Play audio</span>
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                ))
              )}
              <div ref={messagesEndRef} />
            </div>
          </section>

          {/* Recent People */}
          <section className="md:col-span-5 flex flex-col bg-slate-900/50 border border-slate-800 rounded-2xl p-4 min-h-[350px]">
            <h2 className="text-sm font-semibold text-slate-200 pb-3 border-b border-slate-800/80 flex items-center justify-between">
              <span>Recent People</span>
              <span className="text-[11px] font-normal text-slate-400">
                {people.length} saved
              </span>
            </h2>

            <div className="flex-1 overflow-y-auto py-3 space-y-2.5">
              {people.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-center text-slate-500 py-10 px-4">
                  <User className="w-8 h-8 mb-2 opacity-30 text-indigo-400" />
                  <p className="text-xs">No people recorded yet.</p>
                  <p className="text-[11px] text-slate-600 mt-1">
                    When you speak about contacts, they will appear here.
                  </p>
                </div>
              ) : (
                people.map((person) => {
                  const topicsStr = person.topics && person.topics.length > 0 ? person.topics.join(', ') : '';
                  const recs = (person as any).recommendations || [];

                  return (
                    <div
                      key={person.id}
                      className="p-3 bg-slate-950/70 border border-slate-800 rounded-xl hover:border-slate-700 transition"
                    >
                      <div className="flex items-baseline gap-2">
                        <span className="font-semibold text-slate-100 text-xs">- {person.name}</span>
                        {person.company && (
                          <span className="text-slate-400 text-xs font-normal">
                            — {person.company}
                          </span>
                        )}
                        {topicsStr && (
                          <span className="text-indigo-300 text-xs font-normal">
                            — {topicsStr}
                          </span>
                        )}
                      </div>

                      {/* Recommendations if any */}
                      {recs.length > 0 && (
                        <div className="mt-1.5 text-[11px] text-amber-300/90 flex items-center gap-1">
                          <span className="font-medium">Recommended:</span>
                          <span>
                            {recs.map((r: any) => (typeof r === 'string' ? r : r.content)).join('; ')}
                          </span>
                        </div>
                      )}
                    </div>
                  );
                })
              )}
            </div>
          </section>

        </div>

      </div>
    </div>
  );
};
