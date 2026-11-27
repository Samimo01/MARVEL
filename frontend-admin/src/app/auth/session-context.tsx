import { createContext, useContext, type ReactNode } from "react";

export type UserSession = {
  id_user: string;
  user: {
    id_user: string;
    firstname: string;
    lastname: string;
    nickname?: string | null;
    email: string;
    tel?: string | null;
    image_url?: string | null;
    active: boolean;
    created_at: string;
  };
  roles: string[];
};

const SessionContext = createContext<UserSession | null>(null);
export function SessionProvider({
  session,
  children,
}: {
  session: UserSession;
  children: ReactNode;
}) {
  return (
    <SessionContext.Provider value={session}>
      {children}
    </SessionContext.Provider>
  );
}
export function useSession() {
  const value = useContext(SessionContext);
  if (!value)
    throw new Error(
      "useSession doit être utilisé dans le contexte du back-office.",
    );
  return value;
}
