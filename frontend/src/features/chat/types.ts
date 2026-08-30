export type ChatBubble = {
  role: "user" | "assistant";
  content: string;
};

export type StreamChatBody = {
  message: string;
  conversation_id?: string;
};
