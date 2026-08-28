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
