/** Formate un montant en dinars algériens (ex. « 1 500,00 DZD »). */
export function formatAmount(value: number | string): string {
  return new Intl.NumberFormat('fr-DZ', {
    style: 'currency',
    currency: 'DZD',
  }).format(Number(value))
}
