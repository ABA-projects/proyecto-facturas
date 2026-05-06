# TaxOps SaaS MVP — Design Spec

**Date:** 2026-05-06  
**Status:** Approved  
**Scope:** Convert TaxOps from local app to billable SaaS for accounting firms

---

## Context

TaxOps processes Colombian DIAN invoices (PDF/XML) and generates Exógenas reports. It is currently deployed on Railway (`proyecto-facturas-production.up.railway.app`). One pilot client — an accounting firm that manages multiple end-clients — has agreed to pay once the product is ready.

**Goal:** Add auth + multi-tenancy + persistent storage to Railway deployment so the pilot client can log in, use the app with their data isolated, and pay a monthly subscription.

---

## Architecture

```
[Accounting Firm User]  →  Login  →  [TaxOps on Railway]  →  PostgreSQL
                                              │
                                   org_id filters all data
                                   (each firm sees only their own)
```

**Two-mode codebase:**

| Mode | Condition | Behavior |
|------|-----------|----------|
| Local / offline | `DATABASE_URL` not set | App opens directly, no login, no DB |
| SaaS / Railway | `DATABASE_URL` set | Login screen appears, auth enforced, data persisted |

This means zero changes to local development workflow.

---

## Components

### Auth Layer

- **Library:** `streamlit-authenticator`
- **Storage:** PostgreSQL `users` table
- **Session:** `org_id` stored in `st.session_state` after login, passed to all queries
- **Onboarding:** First org + owner user created via CLI/SQL script by operator (no self-signup in MVP)

### Data Model

```sql
organizations (id UUID PK, nombre TEXT, plan TEXT DEFAULT 'starter', created_at TIMESTAMP)
users         (id UUID PK, org_id UUID FK, email TEXT UNIQUE, password_hash TEXT,
               role TEXT CHECK (role IN ('owner','contador')), active BOOLEAN DEFAULT true)
```

Existing `invoices` and `processing_sessions` tables already have `org_id` — no schema changes needed.

### Multi-tenancy

Every DB read/write scopes to `org_id` from session. Owners can add/remove `contador` users within their org. Contadores have full processing access but cannot manage users.

### Persistence

- Invoice processing results saved to `invoices` table (existing schema)
- Exógenas results saved to new `exogenas_results` table (to be added)
- Local mode: results available only as Excel download (unchanged)

### Deployment

- Platform: Railway (already configured)
- PostgreSQL: Railway managed PostgreSQL service (already available)
- Env var: `DATABASE_URL` — presence toggles SaaS mode
- No Docker changes needed for Railway

---

## Pricing — Pilot Agreement

| Period | Price | Notes |
|--------|-------|-------|
| Months 1–3 (pilot) | $150.000 COP/month | 50% discount |
| Month 4+ | $300.000 COP/month | Full price |

**Includes:** Unlimited users within the firm, unlimited invoice/exógenas processing, direct support, early access to new features.

---

## Out of Scope (MVP)

- Self-service signup (operator creates first account manually)
- Stripe / automated billing (invoice manually for now)
- Password reset flow
- Usage analytics per org
- API access

---

## Implementation Order

1. Re-add `sqlalchemy` + `psycopg2-binary` to dependencies (conditional import pattern)
2. Add `streamlit-authenticator` dependency
3. Create `db/auth.py` — user lookup, session setup
4. Add login gate to `Home.py` — only when `DATABASE_URL` present
5. Thread `org_id` through `services/processor.py` and `services/processor_exogenas.py`
6. Scope all DB reads/writes to `org_id`
7. Add `exogenas_results` table to `db/init.sql`
8. Create operator CLI script: `python manage.py create-org`
9. Deploy to Railway and onboard pilot client
10. Agree on pilot pricing and payment method

---

## Success Criteria

- Pilot client logs in on Railway URL with their credentials
- Their processed invoices and exógenas are saved and visible on next login
- No other org can see their data
- Pilot signs payment agreement for 3-month discounted period
