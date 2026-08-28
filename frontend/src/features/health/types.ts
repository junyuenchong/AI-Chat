export type Health = {
  status: string;
  app: string;
  llm: string;
  postgres?: boolean;
  redis?: boolean;
  layers?: Record<string, string>;
};
