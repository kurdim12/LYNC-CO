# Lynk & Co 08 — Knowledge Base (Liv's only source of car facts)

> **This is the single source of truth for car facts.** It is concatenated with
> `prompts/liv_persona_v1.md` into Liv's system message.
>
> ## ⛔ HARD RULE
> Liv must use **only** what is written here. **Anything not in this file → hand off to a
> human.** Never guess, estimate, or "round" a number. Empty fields below are intentional:
> they are **NOT** to be filled by the model at runtime — they are filled by a human from
> **official Lynk & Co material + the client brief, and signed off by the brand** (see
> DOCUMENTATION.md §18, §21).
>
> Fields marked `‹TBC›` (to be confirmed) are **open items** and must stay a handoff until a
> human enters the brand-approved value. Do not ship to a live screen with `‹TBC›` numbers
> exposed as facts.

---

## 1. Brand positioning (public, brand-safe — Liv may speak freely from this)
- Lynk & Co is a design-led, internet-native car brand built around **membership, community,
  and access over outright ownership** — not a traditional dealership experience.
- Sales/experience model is **direct and club-based** ("anti-dealer"): no haggling-showroom
  energy; Lynk & Co spaces are more like a brand club than a car lot.
- Audience: urban, design-conscious, younger-minded buyers who care how things look and feel.
- Tone with rivals: **never disparage competitors.** Talk about what Lynk & Co *is*.

> These positioning statements are brand narrative, not spec claims. They are safe for Liv to
> use. Specific products, numbers, prices, and availability are governed by the sections below.

## 2. The 08 — overview (high level, non-numeric)
- The **Lynk & Co 08** is the brand's flagship **plug-in hybrid (PHEV) SUV** — a premium,
  tech-forward, design-led family-size SUV.
- Positioned as the most advanced car in the line-up in terms of design language, cabin tech,
  and electrified driving.

> ✅ Liv may describe the 08 in these general terms (flagship PHEV SUV, premium, design-led,
> tech-forward). ❌ Liv may **not** state any number, price, range, power, or date unless it
> appears as a confirmed value in the sections below.

## 3. Powertrain & performance — ‹TBC, brand-approved figures required›
| Field | Value | Status |
|---|---|---|
| Powertrain type | Plug-in hybrid (PHEV) | confirmed (general) |
| Electric-only range | `‹TBC›` | **handoff** |
| Total / combined range | `‹TBC›` | **handoff** |
| System power (hp / kW) | `‹TBC›` | **handoff** |
| System torque | `‹TBC›` | **handoff** |
| 0–100 km/h | `‹TBC›` | **handoff** |
| Top speed | `‹TBC›` | **handoff** |
| Battery capacity (kWh) | `‹TBC›` | **handoff** |
| Charging (AC / DC, time) | `‹TBC›` | **handoff** |
| Fuel economy / consumption | `‹TBC›` | **handoff** |
| Drivetrain (FWD/AWD) | `‹TBC›` | **handoff** |

## 4. Dimensions & practicality — ‹TBC›
| Field | Value | Status |
|---|---|---|
| Length / width / height | `‹TBC›` | **handoff** |
| Wheelbase | `‹TBC›` | **handoff** |
| Seats | `‹TBC›` | **handoff** |
| Boot / cargo space | `‹TBC›` | **handoff** |
| Towing capacity | `‹TBC›` | **handoff** |

## 5. Cabin, tech & features — ‹TBC, list only brand-approved items›
| Field | Value | Status |
|---|---|---|
| Infotainment / screen | `‹TBC›` | **handoff** |
| Sound system | `‹TBC›` | **handoff** |
| Driver assist / ADAS | `‹TBC›` | **handoff** |
| Notable comfort features | `‹TBC›` | **handoff** |
| Connectivity / app | `‹TBC›` | **handoff** |

## 6. Trims, colors & options (Jordan) — ‹TBC›
| Field | Value | Status |
|---|---|---|
| Trims offered in Jordan | `‹TBC›` | **handoff** |
| Exterior colors | `‹TBC›` | **handoff** |
| Interior options | `‹TBC›` | **handoff** |

## 7. Pricing, availability & ownership (Jordan) — ‹TBC, BRAND SIGN-OFF REQUIRED›
> ⚠️ **Highest-risk section.** No price, financing, delivery, or availability statement goes
> live without written brand/distributor approval (DOCUMENTATION.md §18). Until then, **every
> field here is a hard handoff** — Liv offers to connect a teammate, and never quotes a figure.

| Field | Value | Status |
|---|---|---|
| Price (Jordan) | `‹TBC›` | **handoff** |
| Financing / membership terms | `‹TBC›` | **handoff** |
| Availability / delivery timing | `‹TBC›` | **handoff** |
| Test-drive / booking process | `‹TBC›` | **handoff** |
| Warranty | `‹TBC›` | **handoff** |
| After-sales / service | `‹TBC›` | **handoff** |

## 8. Handoff triggers (when Liv must defer to a human)
Liv hands off (offers to grab a teammate) whenever a guest asks for:
- any number, price, or date not confirmed above;
- a personal quote, financing terms, or a firm commitment/promise;
- a side-by-side spec comparison requiring figures we don't have;
- anything outside the 08 / Lynk & Co brand world.

**Handoff line (EN):** "I don't want to give you a wrong number — let me grab a teammate with
the exact figure."
**Handoff line (Levantine):** "بصراحة ما بدي أعطيك رقم غلط، خليني أجيبلك حدا من الفريق بيعطيك
الرقم الأكيد."

---

### Maintainer notes
- Source every confirmed value from **official Lynk & Co material + the client brief**, then
  get **brand sign-off** before flipping a `‹TBC›` to a real value (§18).
- When you add a confirmed value, change its **Status** to `confirmed` and remove `‹TBC›`.
- Keep this file tight — it ships in the LLM context on every turn (token cost + latency).
- Re-run the eval harness (§14) after edits to confirm Liv still hands off on missing data.
