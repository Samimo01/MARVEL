import { Card, CardContent } from "@/components/ui/card";
import type { Budget } from "@/features/treasury/types";
export default function BudgetCards({ budget }: { budget: Budget }) {
  const items = [
    { label: "Dons reçus", value: budget.total_donations },
    { label: "Autres recettes", value: budget.total_income },
    { label: "Dépenses", value: budget.total_expenses },
    { label: "Solde", value: budget.balance },
  ];
  return (
    <div className="mb-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      {items.map((item) => (
        <Card key={item.label}>
          <CardContent>
            <p className="text-sm text-gray-500">{item.label}</p>
            <p className="mt-2 text-xl font-semibold text-gray-900 dark:text-white">
              {Number(item.value).toLocaleString("fr-FR")} DA
            </p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
