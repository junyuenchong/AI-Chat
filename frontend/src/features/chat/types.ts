export type ChatBubble = {
  role: "user" | "assistant";
  content: string;
};

export type StreamChatBody = {
  message: string;
  use_rag: boolean;
  conversation_id?: string;
};
