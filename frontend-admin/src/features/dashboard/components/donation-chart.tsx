import Chart from "react-apexcharts";
import type { ApexOptions } from "apexcharts";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

type FinancialPoint = { month: string; amount: number };
type NaturalPoint = { category: string; quantity: number };

export default function DonationChart({
  financial,
  natural,
}: {
  financial: FinancialPoint[];
  natural: NaturalPoint[];
}) {
  const financialOptions: ApexOptions = {
    chart: {
      toolbar: { show: false },
      fontFamily: "Outfit, sans-serif",
      redrawOnParentResize: true,
    },
    colors: ["#465FFF"],
    stroke: { curve: "smooth", width: 3 },
    dataLabels: { enabled: false },
    xaxis: { categories: financial.map((item) => item.month) },
    yaxis: {
      labels: {
        formatter: (value: number) => `${Math.round(value / 1000)}k DA`,
      },
    },
    tooltip: {
      y: {
        formatter: (value: number) => `${value.toLocaleString("fr-FR")} DA`,
      },
    },
    grid: { borderColor: "#E5E7EB", strokeDashArray: 4 },
    responsive: [
      {
        breakpoint: 640,
        options: {
          chart: { height: 280 },
          xaxis: { labels: { rotate: -45 } },
          yaxis: { labels: { style: { fontSize: "10px" } } },
        },
      },
    ],
  };
  const naturalOptions: ApexOptions = {
    chart: {
      toolbar: { show: false },
      fontFamily: "Outfit, sans-serif",
      redrawOnParentResize: true,
    },
    colors: ["#12B76A", "#465FFF", "#F79009", "#F04438", "#7A5AF8"],
    labels: natural.map((item) => item.category),
    dataLabels: {
      enabled: true,
      formatter: (percentage: number) => `${percentage.toFixed(0)}%`,
    },
    legend: { position: "bottom", horizontalAlign: "center" },
    plotOptions: { pie: { donut: { size: "62%" } } },
    tooltip: {
      y: { formatter: (value: number) => `${value} articles` },
    },
    responsive: [
      {
        breakpoint: 640,
        options: {
          chart: { height: 280 },
          legend: { fontSize: "11px", itemMargin: { horizontal: 6 } },
          dataLabels: { style: { fontSize: "11px" } },
        },
      },
    ],
  };

  return (
    <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
      {/* Dons financiers */}
      <Card className="min-w-0">
        <CardHeader>
          <CardTitle>Évolution des dons financiers</CardTitle>
          <CardDescription>
            Montants collectés sur les six derniers mois
          </CardDescription>
        </CardHeader>
        <CardContent className="min-w-0 w-full overflow-hidden">
          <Chart
            type="area"
            height={300}
            width="100%"
            options={financialOptions}
            series={[
              {
                name: "Dons financiers",
                data: financial.map((item) => item.amount),
              },
            ]}
          />
        </CardContent>
      </Card>

      {/* Dons nature */}
      <Card className="min-w-0">
        <CardHeader>
          <CardTitle>Répartition des dons en nature</CardTitle>
          <CardDescription>
            Part des articles collectés par catégorie
          </CardDescription>
        </CardHeader>
        <CardContent className="min-w-0 w-full overflow-hidden">
          <Chart
            type="donut"
            height={300}
            width="100%"
            options={naturalOptions}
            series={natural.map((item) => item.quantity)}
          />
        </CardContent>
      </Card>
    </div>
  );
}
