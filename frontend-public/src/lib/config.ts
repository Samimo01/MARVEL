/** Configuration lue depuis les variables d'environnement Vite (publiques, sans secret). */
export const config = {
  /** Vide en dev (proxy Vite) et en prod derrière le reverse proxy. */
  apiUrl: (import.meta.env.VITE_API_URL as string | undefined) ?? '',
}
