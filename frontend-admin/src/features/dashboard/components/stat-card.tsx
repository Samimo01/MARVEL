import { Card, CardContent } from "@/components/ui/card";
export default function StatCard({
  label,
  value,
  helper,
  icon,
}: {
  label: string;
  value: string;
  helper: string;
  icon: string;
}) {
  return (
    <Card className="min-w-0 gap-3">
      <CardContent className="flex min-w-0 items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-sm text-gray-500 dark:text-gray-400">{label}</p>
          <p className="mt-2 break-words text-2xl font-semibold text-gray-900 dark:text-white">
            {value}
          </p>
          <p className="mt-1 break-words text-xs text-gray-400">{helper}</p>
        </div>
        <span className="flex size-11 shrink-0 items-center justify-center rounded-xl bg-brand-50 text-xl text-brand-600 dark:bg-brand-500/10 dark:text-brand-400">
          {icon}
        </span>
      </CardContent>
    </Card>
  );
}
