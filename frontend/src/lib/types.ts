export type ApiErrorBody = {
  error?: {
    code?: string;
    message?: string;
    fields?: { field?: string; message?: string; type?: string }[];
  };
};

export type TokenResponse = {
  access_token: string;
  token_type: string;
  user_id: string;
  email: string;
  name: string;
};

export type Conversation = {
  id: string;
  title: string;
  summary: string | null;
  created_at: string;
  updated_at: string;
};

export type Message = {
  id: string;
  conversation_id: string;
  role: "user" | "assistant" | string;
  content: string;
  created_at: string;
};

export type ConversationDetail = Conversation & {
  messages: Message[];
};

export type Health = {
  status: string;
  app: string;
  llm: string;
  postgres?: boolean;
  redis?: boolean;
};

export type DocumentOut = {
  id: string;
  filename: string;
  created_at: string;
};
