export type LoginPayload = {
  email: string;
  password: string;
  rememberMe: boolean;
};

export type AuthResponse = {
  message: string;
};
