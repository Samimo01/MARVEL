export const ROLE = {
  volunteer: "Volunteer",
  collection: "Collection_Manager",
  stock: "Stock_Manager",
  treasurer: "Treasurer",
  administrator: "Administrator",
} as const;

export const BACKOFFICE_ROLES = [
  ROLE.collection,
  ROLE.stock,
  ROLE.treasurer,
  ROLE.administrator,
];
export const PAGE_PERMISSIONS: Record<string, string[]> = {
  dashboard: BACKOFFICE_ROLES,
  campaigns: [ROLE.collection, ROLE.administrator],
  financialDonations: [ROLE.collection, ROLE.administrator],
  naturalDonations: [ROLE.collection, ROLE.administrator],
  collects: [ROLE.collection, ROLE.stock, ROLE.administrator],
  stock: [ROLE.stock, ROLE.administrator],
  treasury: [ROLE.treasurer, ROLE.administrator],
  receipts: [ROLE.collection, ROLE.administrator],
  beneficiaries: [ROLE.collection, ROLE.administrator],
  distributions: [ROLE.collection, ROLE.stock, ROLE.administrator],
  missions: [ROLE.collection, ROLE.administrator],
  users: [ROLE.administrator],
  profile: BACKOFFICE_ROLES,
};
export function hasAnyRole(userRoles: string[], allowedRoles: string[]) {
  return userRoles.some((role) => allowedRoles.includes(role));
}
export function canAccessPage(
  userRoles: string[],
  page: keyof typeof PAGE_PERMISSIONS,
) {
  return hasAnyRole(userRoles, PAGE_PERMISSIONS[page]);
}
