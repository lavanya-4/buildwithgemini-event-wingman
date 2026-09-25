export type AgentState = 'IDLE' | 'LISTENING' | 'THINKING' | 'SPEAKING';

export interface Person {
  id: string;
  name: string;
  company?: string;
  role?: string;
  topics: string[];
  notes: string[];
  firstMetAt: string;
  lastInteractionAt: string;
  isDemo?: boolean;
  recommendations?: Recommendation[];
  followups?: FollowUp[];
}

export interface Conversation {
  id: string;
  personIds: string[];
  timestamp: string;
  summary: string;
  topics: string[];
  recommendations: string[];
  ideas: string[];
  rawTranscript?: string;
  isDemo?: boolean;
}

export interface Topic {
  id: string;
  name: string;
  mentionCount: number;
}

export interface Idea {
  id: string;
  title: string;
  description?: string;
  sourcePersonId?: string;
  createdAt: string;
  isDemo?: boolean;
}

export interface Recommendation {
  id: string;
  content: string;
  recommendedByPersonId?: string;
  context?: string;
  createdAt: string;
  isDemo?: boolean;
}

export interface FollowUp {
  id: string;
  personId: string;
  personName?: string;
  personCompany?: string;
  action: string;
  context?: string;
  status: 'draft' | 'approved' | 'cancelled' | 'sent';
  draftMessage?: string;
  createdAt: string;
  isDemo?: boolean;
}

export interface GraphNode {
  id: string;
  label: string;
  type: 'me' | 'person' | 'company' | 'topic' | 'recommendation' | 'idea';
  company?: string;
  role?: string;
  topics?: string[];
  fullText?: string;
  size: number;
  color: string;
  x?: number;
  y?: number;
  vx?: number;
  vy?: number;
}

export interface GraphLink {
  source: string;
  target: string;
  label: string;
  color: string;
}

export interface GraphData {
  nodes: GraphNode[];
  links: GraphLink[];
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'agent' | 'system';
  text: string;
  timestamp: string;
  toolCalls?: Array<{ name: string; args: Record<string, any> }>;
  audioBase64?: string;
}

export interface EventRecap {
  metrics: {
    peopleMet: number;
    conversations: number;
    topics: number;
    ideasCaptured: number;
    followups: number;
    potentialConnections: number;
  };
  topTopics: Topic[];
  recommendations: Recommendation[];
  ideas: Idea[];
  pendingFollowups: FollowUp[];
  potentialConnections: Array<{
    personA: Person;
    personB: Person;
    commonTopics: string[];
    explanation: string;
  }>;
  spokenScript: string;
}

export interface ProactiveInsight {
  type: string;
  title: string;
  message: string;
  actionable: boolean;
}
