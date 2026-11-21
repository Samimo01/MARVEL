import { useState, type InputHTMLAttributes } from 'react'

import { EyeIcon, EyeOffIcon } from '@/components/icons/index.tsx'
import TextInput from '@/components/ui/TextInput.tsx'

type PasswordInputProps = Omit<InputHTMLAttributes<HTMLInputElement>, 'type'> & {
  invalid?: boolean
}

/** Champ mot de passe avec bouton afficher/masquer accessible au clavier. */
export default function PasswordInput({ className = '', ...props }: PasswordInputProps) {
  const [visible, setVisible] = useState(false)

  return (
    <div className="relative">
      <TextInput {...props} type={visible ? 'text' : 'password'} className={`pr-14 ${className}`} />
      <button
        type="button"
        aria-label={visible ? 'Masquer le mot de passe' : 'Afficher le mot de passe'}
        aria-pressed={visible}
        className="absolute right-2 top-1/2 inline-flex h-10 w-10 -translate-y-1/2 items-center justify-center rounded-lg text-muted transition-colors duration-200 hover:bg-foreground/5 hover:text-foreground"
        onClick={() => setVisible((value) => !value)}
      >
        {visible ? <EyeOffIcon className="h-5 w-5" /> : <EyeIcon className="h-5 w-5" />}
      </button>
    </div>
  )
}