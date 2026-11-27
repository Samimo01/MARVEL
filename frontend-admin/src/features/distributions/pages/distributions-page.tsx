import { PageHeading } from "@/components/shared/feature-page";
import { useDistributions } from "@/features/distributions/hooks/use-distributions";
import DistributionTable from "@/features/distributions/components/distribution-table";
export default function DistributionsPage() {
  const { data, loading } = useDistributions();
  return (
    <div>
      <PageHeading
        title="Distributions"
        description="Suivez la préparation et la remise des aides."
      />
      <DistributionTable rows={data ?? []} loading={loading} />
    </div>
  );
}
