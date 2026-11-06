/** Campagne publique, telle que renvoyée par GET /api/v1/public/campaigns.
 *  Les montants (Decimal côté API) arrivent sous forme de chaînes. */
export type Campaign = {
  id: number
  title: string
  description: string
  goal_amount: string
  collected_amount: string
}
