import { PageHeading } from "@/components/shared/feature-page";
import { useBeneficiaries } from "@/features/beneficiaries/hooks/use-beneficiaries";
import BeneficiaryTable from "@/features/beneficiaries/components/beneficiary-table";
export default function BeneficiariesPage() {
  const { data, loading } = useBeneficiaries();
  return (
    <div>
      <PageHeading
        title="Bénéficiaires"
        description="Suivi des dossiers bénéficiaires de l'association."
      />
      <BeneficiaryTable rows={data ?? []} loading={loading} />
    </div>
  );
}
