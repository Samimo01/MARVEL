import { useCallback, useEffect, useState } from "react";

export function useAsyncResource<T>(loader: () => Promise<T>) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const reload = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      setData(await loader());
    } catch (caught) {
      setError(
        caught instanceof Error ? caught.message : "Une erreur est survenue.",
      );
    } finally {
      setLoading(false);
    }
  }, [loader]);

  useEffect(() => {
    void reload();
  }, [reload]);
  return { data, loading, error, reload, setData };
}
