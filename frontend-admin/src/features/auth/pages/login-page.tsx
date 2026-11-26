import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router";
import { useLogin } from "@/features/auth/hooks/use-login";
import LoginForm from "@/features/auth/components/login-form";
import { config } from "@/app/config";

export default function LoginPage() {
  const navigate = useNavigate();
  const { pending, error, signIn } = useLogin();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const authenticated = await signIn({ email, password, rememberMe });
    if (authenticated) navigate("/", { replace: true });
  };

  return (
    <main className="flex min-h-screen items-center justify-center bg-gray-50 px-4 py-12 dark:bg-gray-950">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <a
            href={config.publicUrl.replace(/\/+$/, "")}
            className="mb-7 inline-flex items-center gap-2.5"
            aria-label="MARVEL — retourner au site public"
          >
            <span className="grid size-11 place-items-center rounded-xl bg-brand-500 text-lg font-bold text-white shadow-theme-md">
              M
            </span>
            <span className="text-2xl font-bold tracking-tight text-gray-900 dark:text-white">
              MARVEL
            </span>
          </a>
          <h1 className="text-2xl font-semibold text-gray-900 dark:text-white">
            Connexion au back-office
          </h1>
          <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
            Connectez-vous avec votre compte membre autorisé.
          </p>
        </div>

        <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-theme-lg sm:p-8 dark:border-gray-800 dark:bg-gray-900">
          <LoginForm
            email={email}
            password={password}
            rememberMe={rememberMe}
            pending={pending}
            error={error}
            onEmailChange={setEmail}
            onPasswordChange={setPassword}
            onRememberMeChange={setRememberMe}
            onSubmit={handleSubmit}
          />
          <p className="mt-6 text-center text-xs leading-5 text-gray-500 dark:text-gray-400">
            L’accès est réservé aux membres disposant d’un rôle de gestion
            actif. Si votre compte n’est pas autorisé, contactez un
            administrateur de l’association.
          </p>
        </div>

        <p className="mt-6 text-center text-sm text-gray-500 dark:text-gray-400">
          <a
            href={config.publicUrl.replace(/\/+$/, "")}
            className="font-medium text-brand-600 hover:text-brand-700 dark:text-brand-400"
          >
            Retour au site de l’association
          </a>
        </p>
      </div>
    </main>
  );
}
