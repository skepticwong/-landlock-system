# LandLock — Functional Requirements for Zillow-Level Marketplace

Version: 1.0 · Date: 2026-11-18
Status: Draft — pending build-order sign-off

Scope: New functional requirements to bring LandLock to feature parity with
Zillow-class real-estate platforms (search, discovery, trust, transactions),
while preserving LandLock's differentiators: verified land registry, chief/
official approval workflows, encrypted identity, offline-first submission,
and USSD access.

Non-goals (explicitly out of scope): 3D tours/Street View, mortgage
calculators, rental application screening, iBuying/instant-offer algorithms.

---

## 1. Property Detail Pages (FR-1)

**Priority: P0 — foundation for FR-3, FR-4, FR-5, FR-7**

Every plot gets a dedicated public page at `/plots/[id]`, replacing the
current marketplace modal as the canonical listing view.

| ID     | Requirement                                                                                      |
| ------ | ------------------------------------------------------------------------------------------------ |
| FR-1.1 | Full-page view per plot: photo gallery ( swipe/carousel), description, attributes, price, status |
| FR-1.2 | Interactive map showing the plot's verified boundary polygon, district/TA/village context layers |
| FR-1.3 | Verification panel: chief approval status, authority document verified, identity status of owner |
| FR-1.4 | Price history timeline (listing events, price changes, transfers) from `plot_history`            |
| FR-1.5 | Owner/seller contact block (message, call, chat links respecting contact-sharing rules)          |
| FR-1.6 | "Similar plots nearby" recommendations (same district/TA, similar area band)                     |
| FR-1.7 | Share: copy link, WhatsApp share, generate shareable verification link                           |
| FR-1.8 | Page is server-rendered/SSG-friendly with meta tags for social previews                          |
| FR-1.9 | Unverified/delisted plots show a public "not available" state, never error                       |

## 2. Search & Discovery (FR-2)

**Priority: P0**

| ID     | Requirement                                                                                                                                    |
| ------ | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| FR-2.1 | Faceted filters: price range, area range, district, TA, village, land use, listing type (sale/lease), plot type                                |
| FR-2.2 | Sort: newest, price asc/desc, area asc/desc, distance from map center                                                                          |
| FR-2.3 | Full-text search across plot name, village, landmark description                                                                               |
| FR-2.4 | Pagination or infinite scroll with stable ordering                                                                                             |
| FR-2.5 | Map-first search: search results rendered as boundary polygons on the map, synced with the list panel (hover highlights both)                  |
| FR-2.6 | **Polygon draw search**: user draws an arbitrary region on the map; results filtered by point-in-polygon (reuse `ChiefArea._point_in_polygon`) |
| FR-2.7 | Search state encoded in URL (shareable/back-button-safe)                                                                                       |
| FR-2.8 | Empty and zero-result states with filter suggestions                                                                                           |

## 3. Favorites & Saved Searches (FR-3)

**Priority: P0 — highest retention impact**

| ID     | Requirement                                                                                            |
| ------ | ------------------------------------------------------------------------------------------------------ |
| FR-3.1 | Authenticated users can favorite/unfavorite any listing (heart toggle on cards and detail page)        |
| FR-3.2 | Favorites persist server-side (`favorites` table); optimistic UI update                                |
| FR-3.3 | "Saved plots" page listing all favorites with status changes highlighted                               |
| FR-3.4 | Users can save a search (filters + polygon) with an optional name                                      |
| FR-3.5 | Saved search page; edit/delete searches                                                                |
| FR-3.6 | Alert channels per saved search: in-app notification (mandatory), SMS (opt-in, subject to SMS credits) |
| FR-3.7 | New/changed listings matching a saved search trigger alerts at most once per plot per search (dedupe)  |
| FR-3.8 | Alert generation runs on listing create/update (event-driven, not polling-heavy)                       |

## 4. Listing Quality & Attributes (FR-4)

**Priority: P1**

| ID     | Requirement                                                                                                                                   |
| ------ | --------------------------------------------------------------------------------------------------------------------------------------------- |
| FR-4.1 | Structured attributes per plot: bedrooms, water access, road access, soil type, title type (freehold/leasehold/customary), utilities, fencing |
| FR-4.2 | Attributes stored as a validated JSON column with schema; filter facets derived from it                                                       |
| FR-4.3 | Multi-photo upload per listing with reorder and primary photo selection (extends `listing_images`)                                            |
| FR-4.4 | Optional video walkthrough upload (size-capped, permission-gated)                                                                             |
| FR-4.5 | Listing quality score shown to sellers (photos count, description, attributes filled) with tips                                               |
| FR-4.6 | Draft listings: save incomplete listings, publish when complete                                                                               |
| FR-4.7 | Listing expiry/duration with renewal prompt                                                                                                   |

## 5. Price Intelligence (FR-5)

**Priority: P1 — differentiator; no Malawian competitor has this**

| ID     | Requirement                                                                                                           |
| ------ | --------------------------------------------------------------------------------------------------------------------- |
| FR-5.1 | Price history timeline on detail page (events: listed, repriced, sold/leased)                                         |
| FR-5.2 | "Market range" estimate per plot: derived from comparable sales/leases in the same district/TA with similar area band |
| FR-5.3 | Comparable set shown (3–5 anonymized comparables with distance/area/price)                                            |
| FR-5.4 | Estimate clearly labeled as indicative; hidden if insufficient data (<3 comparables)                                  |
| FR-5.5 | District-level price stats page (median price per m², trend) for officials/public                                     |
| FR-5.6 | Estimate computation is a batch job or view, not per-request heavy query                                              |

## 6. Offers & Transaction Pipeline (FR-6)

**Priority: P1 — extends the existing approval engine**

| ID     | Requirement                                                                                                         |
| ------ | ------------------------------------------------------------------------------------------------------------------- |
| FR-6.1 | Buyer submits an offer on a listing: amount, conditions, preferred completion date                                  |
| FR-6.2 | Seller can accept / decline / counter (one active counter per offer thread)                                         |
| FR-6.3 | Offer statuses visible to both parties with full history log                                                        |
| FR-6.4 | Accepted offer creates a transaction in the existing multi-party approval engine (buyer/seller/witness/chief codes) |
| FR-6.5 | Listing is marked "under offer" while an offer is pending; auto-restored on decline                                 |
| FR-6.6 | Offer notifications via the system toast/notification rail (and SMS for status changes)                             |
| FR-6.7 | Anti-abuse: max open offers per buyer per day                                                                       |

## 7. Trust, Profiles & Disputes (FR-7)

**Priority: P1**

| ID     | Requirement                                                                                                     |
| ------ | --------------------------------------------------------------------------------------------------------------- |
| FR-7.1 | Public seller profile page: active listings, verification level, join date, response rate                       |
| FR-7.2 | Verification badges displayed consistently across all surfaces (registry-verified, ID-verified, chief-approved) |
| FR-7.3 | Buyer→seller ratings after completed transactions (1–5 + text, one review per transaction)                      |
| FR-7.4 | Ratings shown on seller profile and listing cards                                                               |
| FR-7.5 | Public dispute status on plots under dispute (from chief disputed queue), with anonymized case summary          |
| FR-7.6 | Report listing flow (flag → admin moderation queue)                                                             |

## 8. Payments (FR-8)

**Priority: P1 — gateway to monetization**

| ID     | Requirement                                                                                              |
| ------ | -------------------------------------------------------------------------------------------------------- |
| FR-8.1 | Replace mock payment flow with Airtel Money + TNM Mpamba merchant APIs                                   |
| FR-8.2 | Payment categories: transfer fee (existing), listing fee (optional per policy), featured listing upgrade |
| FR-8.3 | Payment states: initiated → pending → confirmed/failed, with reconciliation                              |
| FR-8.4 | Payment receipt stored and viewable in user's transaction history                                        |
| FR-8.5 | Refund/cancellation handling for failed transfers                                                        |
| FR-8.6 | Sandbox/test mode toggle via env config                                                                  |

## 9. Notifications & Communication (FR-9)

**Priority: P1 — builds directly on the new system-styled notification rail**

| ID     | Requirement                                                                                                                        |
| ------ | ---------------------------------------------------------------------------------------------------------------------------------- |
| FR-9.1 | All user-facing confirmations/errors use the system-styled toasts/dialogs (completed for current flows; keep for all new features) |
| FR-9.2 | In-app notification center (exists) gains: offer events, favorite status changes, saved-search alerts, dispute updates             |
| FR-9.3 | Notification preferences page: per-category opt-in/out of in-app and SMS                                                           |
| FR-9.4 | Email channel optional (deferred until domain/email infra exists)                                                                  |

## 10. Identity, Permissions & Representation (FR-10)

**Priority: P2**

**Design principle: one account per person, for life.** Users never switch
account types. Growing needs are handled by granting *permissions on
resources*, not by creating a second identity. What is modeled separately:
who the user **is** (identity), which organization they **represent**
(membership), and what they're allowed to do **and where** (scoped grants).

| ID      | Requirement                                                                                                                          |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| FR-10.1 | Single personal account for everything: browse, buy, save, own, list. Any account may list property it owns once verified — no "agent signup" |
| FR-10.2 | **Scoped representation grants**: an owner grants another user permission to manage specific plots/listings (list, edit, respond to offers) — never blanket access to the whole portfolio |
| FR-10.3 | Grant lifecycle: owner-initiated consent (link/code), viewable and revocable by the owner at any time; grants expire by default          |
| FR-10.4 | Grants are role-flavored: "list for me", "co-manage", "respond to inquiries" — the grant defines capability, not a new user role          |
| FR-10.5 | **Business profiles (organizations)**: a verified company profile can own listings; team members link their personal accounts to it       |
| FR-10.6 | Organization members get permissions assigned within the org (owner / manager / listing agent); actions taken on behalf of the org are attributed both to the member and the org |
| FR-10.7 | Business verification: org registration doc reviewed by admin before the org profile is marked verified (mirrors existing identity verification) |
| FR-10.8 | **Special trust roles stay distinct**: valuer, chief, official, admin — these are verified authorities whose powers come from the state/org, not from a listing relationship; they are additive permissions on the personal account, not account types |
| FR-10.9 | Valuer submits valuation reports against specific plots (permission granted by admin/official assignment, not self-claimed)             |
| FR-10.10 | Role-based dashboard views are composed from permissions (a user sees agent tools only if they hold active grants or org membership)   |
| FR-10.11 | Admin moderation queue for reports, reviews, listings, org verifications, and valuer assignments                                      |
| FR-10.12 | Audit trail: every listing-modifying action records which user performed it, under which grant or org membership                      |

## 11. Non-Functional Requirements (NFR)

| ID    | Requirement                                                                                                      |
| ----- | ---------------------------------------------------------------------------------------------------------------- |
| NFR-1 | Migrate backend SQLite → Supabase/Postgres before public launch (scaffold exists in `db/supabase.py`)            |
| NFR-2 | All new endpoints enforce auth + role checks; no new unauthenticated mutation endpoints                          |
| NFR-3 | File uploads size-capped and type-validated (existing 11 MB body limit maintained)                               |
| NFR-4 | Search/filter endpoints paginated (default 20, max 100)                                                          |
| NFR-5 | All user-facing messages system-styled (no native browser dialogs) — enforced by convention                      |
| NFR-6 | Mobile-first responsive: marketplace, detail page, saved pages must be fully usable on low-end Android           |
| NFR-7 | Offline behavior: favorites/alerts degrade gracefully (queued actions where feasible)                            |
| NFR-8 | USSD parity review: key citizen actions (search summary, saved search opt-in) reachable via USSD where practical |

---

## Data model additions (summary)

- `favorites(user_id, listing_id, created_at)` — unique(user_id, listing_id)
- `saved_searches(id, user_id, name, query_json, polygon_json, channels, created_at)`
- `saved_search_alerts(search_id, listing_id, sent_at)` — dedupe
- `plot_attributes(plot_id, attrs_json)` — validated schema
- `offers(id, listing_id, buyer_id, amount, conditions, status, thread_id, created_at)`
- `reviews(tx_id, reviewer_id, reviewee_id, score, text, created_at)`
- `reports(id, target_type, target_id, reporter_id, reason, status)`
- `payment_receipts` (extends existing `payments`)
- `representation_grants(id, owner_id, grantee_id, plot_id, capability, status, expires_at, created_by, created_at)` — scoped, revocable, expiring
- `organizations(id, name, reg_number, verification_status, verified_by, verified_at)`
- `org_members(org_id, user_id, member_role, added_by, created_at)`
- `audit_log(id, actor_id, on_behalf_of (user|org), grant_id, action, target_type, target_id, created_at)`

## Suggested build order

1. FR-1 detail page (foundation)
2. FR-3.1–3.3 favorites
3. FR-2.1–2.4, 2.7, 2.8 core search facets
4. FR-3.4–3.8 saved searches + alerts
5. FR-2.5–2.6 map/polygon search
6. FR-5 price history + market range
7. FR-4 attributes + listing quality
8. FR-6 offers pipeline
9. FR-8 payments
10. FR-7 profiles/reviews/disputes
11. FR-10.1–10.4 scoped representation grants (agents without new account types)
12. FR-10.5–10.7 business profiles & org teams
13. FR-10.8–10.12 trust roles, valuer assignments, audit trail
