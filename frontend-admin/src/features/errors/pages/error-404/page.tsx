import { PageMeta } from "@/components/shared/page-meta";
import Error404 from "./index";

export default function Error404Page() {
  return (
    <div>
      <PageMeta
        title="Page introuvable | MARVEL"
        description="La page demandée est introuvable."
      />
      <Error404 />
    </div>
  );
}
