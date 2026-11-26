import type { ReactNode } from "react";
import { PageBreadcrumb } from "@/components/shared/page-breadcrumb";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

export type Column<T> = {
  key: keyof T | string;
  label: string;
  render?: (row: T) => ReactNode;
};
export function PageHeading({
  title,
  description,
  action,
}: {
  title: string;
  description: string;
  action?: ReactNode;
}) {
  return (
    <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <PageBreadcrumb pageTitle={title} />
        <p className="-mt-4 text-sm text-gray-500 dark:text-gray-400">
          {description}
        </p>
      </div>
      {action}
    </div>
  );
}
export function DataPanel<T extends object>({
  title,
  description,
  rows,
  columns,
  loading = false,
  empty = "Aucune donnée à afficher.",
  badge,
}: {
  title: string;
  description?: string;
  rows: T[];
  columns: Column<T>[];
  loading?: boolean;
  empty?: string;
  badge?: string;
}) {
  return (
    <Card>
      <CardHeader className="flex-row items-start justify-between">
        <div>
          <CardTitle>{title}</CardTitle>
          {description && <CardDescription>{description}</CardDescription>}
        </div>
        {badge && <Badge color="info">{badge}</Badge>}
      </CardHeader>
      <CardContent className="overflow-x-auto p-0">
        <table className="w-full min-w-[640px] text-start text-sm">
          <thead>
            <tr className="border-y border-gray-100 bg-gray-50 text-xs uppercase tracking-wide text-gray-500 dark:border-gray-800 dark:bg-white/3 dark:text-gray-400">
              {columns.map((column) => (
                <th
                  key={String(column.key)}
                  className="px-5 py-3 text-start font-medium"
                >
                  {column.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
            {loading ? (
              <tr>
                <td
                  colSpan={columns.length}
                  className="px-5 py-10 text-center text-gray-500"
                >
                  Chargement…
                </td>
              </tr>
            ) : rows.length === 0 ? (
              <tr>
                <td
                  colSpan={columns.length}
                  className="px-5 py-10 text-center text-gray-500"
                >
                  {empty}
                </td>
              </tr>
            ) : (
              rows.map((row, index) => (
                <tr
                  key={String(
                    (row as Record<string, unknown>).id ??
                      (row as Record<string, unknown>).id_campaign ??
                      (row as Record<string, unknown>).id_don_f ??
                      (row as Record<string, unknown>).id_don_n ??
                      (row as Record<string, unknown>).id_collect ??
                      (row as Record<string, unknown>).id_mission ??
                      index,
                  )}
                  className="text-gray-700 dark:text-gray-300"
                >
                  {columns.map((column) => (
                    <td key={String(column.key)} className="px-5 py-4">
                      {column.render
                        ? column.render(row)
                        : String(
                            (row as Record<string, unknown>)[
                              String(column.key)
                            ] ?? "—",
                          )}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </CardContent>
    </Card>
  );
}
export function ActionButton({
  children,
  onClick,
  disabled = false,
  variant = "default",
}: {
  children: ReactNode;
  onClick: () => void;
  disabled?: boolean;
  variant?: "default" | "outline" | "destructive";
}) {
  return (
    <Button onClick={onClick} disabled={disabled} variant={variant}>
      {children}
    </Button>
  );
}
export function StatusPill({ value }: { value: string }) {
  const normalized = value.toLowerCase();
  const color = [
    "active",
    "published",
    "publish",
    "success",
    "succeeded",
    "validated",
    "completed",
    "received",
    "confirmed",
    "in_progress",
    "in_stock",
    "done",
    "valid",
  ].some((part) => normalized.includes(part))
    ? "success"
    : ["pending", "draft", "planned", "waiting", "declare", "valid"].some(
          (part) => normalized.includes(part),
        )
      ? "warning"
      : ["rejected", "cancelled", "failed", "closed", "inactive"].some((part) =>
            normalized.includes(part),
          )
        ? "error"
        : "light";
  return (
    <Badge color={color as "success" | "warning" | "error" | "light"}>
      {value}
    </Badge>
  );
}
