export type ChatRole = "user" | "assistant";

export type ChatSource = {
  source_id: string;
  source_type: string;
  title: string | null;
  date: string | null;
  evidence: string;
  evidence_label?: string;
  relevance_score?: number;
  trusted_source_reference: {
    location: string | null;
    web_url: string | null;
    file_path: string | null;
    parent_location: string | null;
    metadata: Record<string, unknown> | null;
  };
};

export type RagAnswerResponse = {
  query: string;
  answer: string;
  status: "answered" | "no_results";
  sources: ChatSource[];
};

export type ChatMessage = {
  id: string;
  role: ChatRole;
  content: string;
  timestamp: string;
  sources?: ChatSource[];
  isError?: boolean;
  retryQuery?: string;
  noResults?: boolean;
  answerMode?: "ask" | "search";
};
