import type { FormEvent } from "react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

type LoginFormProps = {
  email: string;
  password: string;
  rememberMe: boolean;
  pending: boolean;
  error: string;
  onEmailChange: (value: string) => void;
  onPasswordChange: (value: string) => void;
  onRememberMeChange: (value: boolean) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
};

export default function LoginForm({
  email,
  password,
  rememberMe,
  pending,
  error,
  onEmailChange,
  onPasswordChange,
  onRememberMeChange,
  onSubmit,
}: LoginFormProps) {
  return (
    <form className="space-y-5" onSubmit={onSubmit}>
      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <div className="space-y-2">
        <Label htmlFor="login-email">Adresse e-mail</Label>
        <Input
          id="login-email"
          type="email"
          name="email"
          placeholder="nom@exemple.com"
          autoComplete="username"
          value={email}
          onChange={(event) => onEmailChange(event.target.value)}
          required
          disabled={pending}
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="login-password">Mot de passe</Label>
        <Input
          id="login-password"
          type="password"
          name="password"
          placeholder="Saisissez votre mot de passe"
          autoComplete="current-password"
          value={password}
          onChange={(event) => onPasswordChange(event.target.value)}
          required
          disabled={pending}
        />
      </div>

      <div className="flex items-center gap-2">
        <Checkbox
          id="remember-me"
          checked={rememberMe}
          onCheckedChange={(checked) => onRememberMeChange(checked === true)}
          disabled={pending}
        />
        <Label htmlFor="remember-me" className="cursor-pointer font-normal">
          Se souvenir de moi
        </Label>
      </div>

      <Button type="submit" className="w-full" size="lg" disabled={pending}>
        {pending ? "Connexion en cours…" : "Se connecter"}
      </Button>
    </form>
  );
}
