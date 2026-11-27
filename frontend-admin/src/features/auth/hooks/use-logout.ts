import { useState } from "react";
import { logout } from "@/features/auth/api";

export function useLogout() {
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");

  const signOut = async () => {
    setPending(true);
    setError("");
    try {
      await logout();
      return true;
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Impossible de se déconnecter.",
      );
      setPending(false);
      return false;
    }
  };

  return { pending, error, signOut };
}
