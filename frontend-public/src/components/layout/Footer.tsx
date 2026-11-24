export const PUBLIC_FOOTER_TEXT = '© Association caritative — Projet DevOps'

export default function Footer({
  text = PUBLIC_FOOTER_TEXT,
}: {
  text?: string
}) {
  return (
    <footer className="border-t border-border bg-surface py-4 text-center text-sm text-muted">
      {text}
    </footer>
  )
}
