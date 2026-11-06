import type { ReactNode } from 'react'

export default function PageContainer({ children }: { children: ReactNode }) {
  return <main className="mx-auto w-full max-w-5xl flex-1 px-4 py-8">{children}</main>
}
