export type ChatRole = "user" | "assistant";

export type ChatSource = {
  id: string;
  title: string;
  type: string;
  summary: string;
  date: string;
  category: string;
};

export type ChatMessage = {
  id: string;
  role: ChatRole;
  content: string;
  timestamp: string;
  sources?: ChatSource[];
  isError?: boolean;
  retryQuery?: string;
};
