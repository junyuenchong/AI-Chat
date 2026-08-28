export type AuthMode = "login" | "register";

export type UserProfile = {
  id: string;
  email: string;
  name: string;
};

export type TokenResponse = {
  access_token: string;
  token_type: string;
  user_id: string;
  email: string;
  name: string;
};
