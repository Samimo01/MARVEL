# MARVEL frontend cleanup notes

## Phase 1: demo-page cleanup

### Removed
- E-commerce dashboard demo and its page-specific charts, metrics, maps, and sample orders.
- Calendar demo.
- Form-elements demo page and its page-specific examples.
- Basic-tables demo page and its page-specific sample tables.
- Chart demo pages.
- UI-elements demo pages (alerts, avatars, badges, buttons, images, videos).
- Sign-in and sign-up demo pages.
- Blank-page demo.

### Kept intentionally
- Shared UI primitives in `src/components/ui/`.
- Shared layout, sidebar, header, theme, and scroll components.
- Icon components and public assets, pending the branding phase.
- Profile page as a temporary reusable starting point; its sample data still needs to be replaced.
- 404 page.
- Existing dependencies and global CSS. Dependency and CSS pruning are deferred until remaining shared-component usage is audited.

### Current routes
- `/` — Administration dashboard placeholder.
- `/profile` — temporary profile page.
- `/error-404` and fallback — 404 page.

### Notes
- The dashboard placeholder introduces no business logic or fabricated metrics.
- The sidebar now contains only Dashboard and Profile.
- The sign-out demo action was removed because real authentication is not integrated yet.
- The user menu now displays a generic administrator identity instead of TailAdmin sample personal data.

## Validation

`npm run build` could not be completed in the provided environment because `npm ci` did not finish before the execution timeout. The partial dependency installation also left TypeScript unable to resolve the Vite and Node type definitions. Re-run `npm ci` in the project environment, then `npm run build`.


## Phase 2 — Architectural restructuring

- Migration of the admin layout to `src/layouts/admin-layout/`.
- Migration of the dashboard, profile, and 404 page to `src/features/`.
- Centralization of routing in `src/app/router/`.
- Relocation of the `ThemeProvider` to `src/app/providers/`.
- Move still-used images to `src/assets/` and then remove `public/` conten (except favicon.png).
- Add French while keeping the English and Arabic resources.