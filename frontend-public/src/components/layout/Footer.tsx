export default function Footer({ text }: { text: string }) {
  return (
    <footer className="border-t border-border bg-surface py-4 text-center text-sm text-muted">
      {text}
    </footer>
  )
}
