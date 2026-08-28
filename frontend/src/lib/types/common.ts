/** Shared API error shape returned by the FastAPI backend. */
export type ApiErrorBody = {
  error?: {
    code?: string;
    message?: string;
    fields?: { field?: string; message?: string; type?: string }[];
  };
};
