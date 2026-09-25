import { EventRecap, FollowUp, GraphData, Idea, Person, ProactiveInsight, Recommendation, Topic } from '../types';

const API_BASE = '/api';

export async function sendChatMessage(message: string, includeAudio: boolean = true) {
  const res = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, include_audio: includeAudio }),
  });
  if (!res.ok) throw new Error(`Chat error: ${res.statusText}`);
  return res.json();
}

export async function processAudioFile(audioBlob: Blob) {
  const formData = new FormData();
  formData.append('file', audioBlob, 'mic_recording.webm');
  const res = await fetch(`${API_BASE}/voice/process-audio`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) throw new Error(`Audio processing error: ${res.statusText}`);
  return res.json();
}

export async function fetchPeople(): Promise<Person[]> {
  const res = await fetch(`${API_BASE}/memory/people`);
  return res.json();
}

export async function fetchPerson(id: string): Promise<Person> {
  const res = await fetch(`${API_BASE}/memory/people/${id}`);
  return res.json();
}

export async function deletePerson(id: string): Promise<void> {
  await fetch(`${API_BASE}/memory/people/${id}`, { method: 'DELETE' });
}

export async function fetchConversations() {
  const res = await fetch(`${API_BASE}/memory/conversations`);
  return res.json();
}

export async function fetchTopics(): Promise<Topic[]> {
  const res = await fetch(`${API_BASE}/memory/topics`);
  return res.json();
}

export async function fetchIdeas(): Promise<Idea[]> {
  const res = await fetch(`${API_BASE}/memory/ideas`);
  return res.json();
}

export async function fetchRecommendations(): Promise<Recommendation[]> {
  const res = await fetch(`${API_BASE}/memory/recommendations`);
  return res.json();
}

export async function fetchFollowups(): Promise<FollowUp[]> {
  const res = await fetch(`${API_BASE}/memory/followups`);
  return res.json();
}

export async function approveFollowup(id: string): Promise<FollowUp> {
  const res = await fetch(`${API_BASE}/memory/followups/${id}/approve`, { method: 'POST' });
  return res.json();
}

export async function cancelFollowup(id: string): Promise<FollowUp> {
  const res = await fetch(`${API_BASE}/memory/followups/${id}/cancel`, { method: 'POST' });
  return res.json();
}

export async function updateFollowupDraft(id: string, draftMessage: string): Promise<FollowUp> {
  const res = await fetch(`${API_BASE}/memory/followups/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ draft_message: draftMessage }),
  });
  return res.json();
}

export async function regenerateFollowup(id: string, tone = 'friendly_professional'): Promise<FollowUp> {
  const res = await fetch(`${API_BASE}/memory/followups/${id}/regenerate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ tone }),
  });
  return res.json();
}

export async function fetchNetworkGraph(): Promise<GraphData> {
  const res = await fetch(`${API_BASE}/network/graph`);
  return res.json();
}

export async function fetchRelatedPeople(query: string) {
  const res = await fetch(`${API_BASE}/network/related?query=${encodeURIComponent(query)}`);
  return res.json();
}

export async function fetchInsights(): Promise<ProactiveInsight[]> {
  const res = await fetch(`${API_BASE}/network/insights`);
  return res.json();
}

export async function fetchEventRecap(): Promise<EventRecap> {
  const res = await fetch(`${API_BASE}/recap`);
  return res.json();
}

export async function seedDemoData() {
  const res = await fetch(`${API_BASE}/memory/demo/seed`, { method: 'POST' });
  return res.json();
}

export async function clearDemoData() {
  const res = await fetch(`${API_BASE}/memory/demo/clear`, { method: 'POST' });
  return res.json();
}

export async function clearAllMemories() {
  const res = await fetch(`${API_BASE}/memory/clear`, { method: 'POST' });
  return res.json();
}
