import { HeartIcon } from '@/components/icons/index.tsx'

type AuthFormHeadingProps = {
  title: string
  description: string
}

export default function AuthFormHeading({ title, description }: AuthFormHeadingProps) {
  return (
    <div className="mb-6 flex items-center gap-3">
      <span
        aria-hidden="true"
        className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-foreground text-primary shadow-lg"
      >
        <HeartIcon className="h-5 w-5" />
      </span>
      <div className="min-w-0">
        <h1 className="text-xl font-black tracking-tight sm:text-2xl">{title}</h1>
        <p className="mt-1 text-sm text-muted">{description}</p>
      </div>
    </div>
  )
}
