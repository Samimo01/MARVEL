const isDevelopment = import.meta.env.DEV

export const config = {
  apiUrl: (import.meta.env.VITE_API_URL as string | undefined) ?? '',
  publicUrl:
    (import.meta.env.VITE_PUBLIC_URL as string | undefined) ??
    (isDevelopment ? 'http://localhost:5173' : 'http://localhost:8080'),
}
