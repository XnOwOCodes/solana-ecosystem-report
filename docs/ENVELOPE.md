# Envelope
## On-chain spend policy for AI agents paying over x402 on Solana

**Ideathon submission — Superteam Ukraine / Colosseum Hackathon**
**Sector:** AI Agents and Machine Payments
**One-liner:** Give an operator a USDC envelope an agent can spend, with on-chain caps, merchant allowlists, and an automatic pause — without locking to Crossmint, Coinbase, or any single wallet vendor.

Research date: 25 Aug 2026.
Sources used (not a literature dump — these are the facts the idea hangs on):
- Solana Foundation + Coinbase, “Agentic Payments” webinar recap: x402 ~200M tx, ~$50B volume, ~150k merchant endpoints; most payments under $0.50. Solana stablecoins >$15B circulating. https://solana.com/news/webinar-recap-agentic-payments
- Token Terminal / CryptoBriefing, Aug 2026: 3.3M USDC x402 transfers on Solana in one week; Solana ~70% of x402 volume; typical tx <$0.50. https://cryptobriefing.com/ai-agents-x402-usdc-solana-transfers/
- Solana docs: x402 + Kora gasless facilitator, USDC payment without holding SOL. https://solana.com/docs/payments/agentic-payments/x402-facilitator
- pay.sh: live Solana CLI directory of x402-payable endpoints (demo’d in the webinar).
- Wallet landscape 2026: Crossmint dual-key + TEE, Coinbase Agentic Wallets (Feb 2026), Skyfire KYA, ERC-7715 session permissions on EVM. Spend policy exists — it is not portable across runtimes or x402 merchants.

---

### problemStatement

x402 solved “how does an agent pay for an HTTP resource.” It did not solve “how does the human who is on the hook for that wallet stop the agent from lighting the treasury.”

Who feels it, today:

1. **The operator of a coding / research agent** (Cursor, Claude Code, OpenClaw). The agent can already hit pay.sh, Exa, Browserbase and pay a cent per call. There is no portable way to say: “this agent may spend $8/day, only to these facilitators, and freeze if it spikes 10x.” Today that policy lives inside one vendor’s wallet (Crossmint caps, Coinbase TEE rules) or inside the agent’s prompt (which is not a control).
2. **Anyone who lets an agent both earn and spend from the same key.** Compromised session = drained earnings. EVM has ERC-7715 session keys. Solana’s x402 stack (Kora + facilitator + wrapFetchWithPayment) signs with a payer key that can spend whatever USDC it holds.
3. **Merchants accepting x402.** They see a flood of sub-$0.50 agent traffic and have no standard way to require “this agent is spending from a policy-bounded envelope,” which is the difference between a customer and a runaway loop.

The pain is not theoretical. x402 volume is micropayments at machine speed. A bug that retries a 10¢ tool 2,000 times is a $200 hole in one session, settled in USDC before a human notices. Card networks had authorization holds and MCC blocks for this. Agents on Solana currently have “hope the prompt is careful.”

This is not “we need another agent wallet.” Wallets exist. What’s missing is a **Solana-native, vendor-neutral spend envelope** that any x402 client can be forced through.

---

### technicalApproach

Envelope is three pieces, sized for a hackathon:

**1. Solana program (Anchor) — the Envelope account**

- PDA per `(operator, agent_id)`.
- Fields: `authority` (operator), `agent_session` (pubkey the agent signs with), `token_mint` (USDC), `balance`, `max_per_tx`, `max_per_window`, `window_secs`, `spent_in_window`, `window_started_at`, `allowlist` (up to N pay-to / facilitator pubkeys), `paused`, `expires_at`.
- Instructions:
  - `create` / `fund` (operator deposits USDC into the PDA’s ATA)
  - `set_policy` (operator only)
  - `spend` — CPI token transfer to a pay-to address **only if** amount ≤ max_per_tx, window not exceeded, payee in allowlist, not paused, not expired. Increments `spent_in_window`.
  - `pause` / `sweep` (operator recovers leftover USDC)
- No SOL required from the agent: `spend` is invoked via a Kora-style facilitator as fee payer, same pattern as the official x402+Kora demo. Agent signs the spend ix; Kora pays gas; USDC moves from the Envelope ATA.

**2. x402 client shim — `envelope-fetch`**

Replace `wrapFetchWithPayment(fetch, payerKey)` with `wrapFetchWithEnvelope(fetch, envelopePda, agentSession)`.

On HTTP 402:
- Parse payment requirements (amount, pay-to, network).
- If the pay-to is not on the on-chain allowlist, refuse locally (don’t even hit the chain).
- Build `spend` ix instead of a raw USDC transfer from the agent’s wallet.
- Submit via the existing facilitator `/verify` + `/settle` path.

This is the integration that makes Envelope real rather than a toy program: it sits where agents already pay (the 402 retry loop).

**3. Operator CLI / tiny dashboard**

```
envelope create --daily 8 --max-tx 0.50 --allow pay.sh,exa,browserbase
envelope fund 20
envelope status   # on-chain remaining, spent-in-window, last 10 spends
envelope pause
```

Status is a single `getAccountInfo` + parsed token balance. Optional: anomaly pause if spent-in-window jumps >Nx vs the previous window (client-side watcher, not required in v0).

**Protocols we actually plug into (not a name-drop list):**

- **x402** for the HTTP payment handshake (402 → X-PAYMENT).
- **Kora** as gasless facilitator so the agent key never holds SOL.
- **USDC (SPL)** as the only mint in v0.
- **pay.sh** as the first live merchant directory for the demo: one protected call, one Envelope spend, one on-chain receipt.

**Hackathon demo (end-to-end, one laptop):**

1. Operator creates an Envelope with `$1` daily cap, `$0.05` max per tx, allowlist = the demo API’s pay-to.
2. Agent calls a protected endpoint without payment → 402.
3. Agent retries via `envelope-fetch` → spend succeeds, 200, receipt signature.
4. Agent retries 30 times → 3rd call fails on-chain (`max_per_tx` or window). Dashboard shows paused/exhausted. Raw wallet spend is impossible because the USDC is in the PDA, not the agent key.

That’s a Colosseum-sized slice. Not a wallet company.

**Out of scope for the hackathon, named so we don’t fake it:** cards, EVM, KYC, “Know Your Agent,” yield on idle envelope balances.

---

### targetAudience

**First user:** a developer already running an agent that pays for tools (Claude Code / Cursor / OpenClaw) who has funded a Solana USDC address for x402.

**Current workflow:**
1. Put USDC in a hot key the agent can sign with.
2. Point the agent at pay.sh / x402-wrapped fetch.
3. Hope. Check the explorer later. If the agent loops, revoke the key after the fact.

**Workflow with Envelope:**
1. `envelope create --daily 8 --allow <facilitators>`
2. `envelope fund 20`
3. Point the agent at `envelope-fetch` instead of the raw payer.
4. Get a Slack/CLI ping when the window is 80% spent or a spend is rejected.

We are not asking this person to switch wallets, pass KYC, or move off Solana. They already have USDC and an agent. We only change *which instruction* the 402 retry submits.

**Deliberately not first:** enterprises, consumer “AI shopping” apps, merchants. Those are later distribution, not the first 10 users.

---

### businessModel

Hackathon / OSS: Apache-2.0 program + shim. No token.

Sustainable shape after that, in order of honesty:

1. **Hosted facilitator with Envelope baked in.** Operators who don’t want to run Kora pay a flat $20–50/mo, or 30–50 bps on funded envelopes. This is the same job Kora already does, plus policy. Margin is ops, not gas.
2. **Merchant-side “require Envelope”.** Once a few agents use it, APIs can reject raw payer keys and only settle spends from Envelope PDAs (program-derived proof the spend was capped). Charge merchants like fraud-filter SaaS.
3. **Not** TVL yield, not a launchpad, not taking a cut of every 0.3¢ API call — x402 already has facilitator economics and the tx size is too small to stack another fee without killing the use case.

If we cannot get 50 operators to fund an Envelope in 90 days, the product is wrong; we don’t pivot into a memecoin.

---

### competitiveLandscape

| What exists | What it actually does | Why Envelope is not that |
|---|---|---|
| **x402 + Kora + pay.sh** | Pay-per-request USDC, gasless, open standard | No operator cap. Payer key = full balance. Envelope *uses* this stack; it does not replace it. |
| **Crossmint agent wallets** | Dual-key, TEE, per-tx/daily caps, cards + USDC, 40+ chains | Excellent, and vendor-locked. Policy is inside Crossmint. An OpenClaw agent paying a random x402 merchant on Solana does not inherit those caps unless the whole stack is Crossmint. |
| **Coinbase Agentic Wallets (Feb 2026)** | TEE + x402, EVM and Solana | Same: policy lives in Coinbase’s wallet, not in a program any client can be forced through. |
| **Skyfire KYA** | Agent identity / credentials for merchants | Identity ≠ spend cap. Complementary. Envelope can later require a KYA token; v0 does not. |
| **Nevermined** | Metering and merchant entitlements | Merchant-side billing. Envelope is operator-side budget. |
| **ERC-7715 session keys (EVM)** | Scoped permissions on smart accounts | Right idea, wrong chain for x402’s actual volume (Solana ~70%). We are the Solana-shaped version, scoped to USDC x402 spends, not a general session-key protocol. |
| **Prompt-level budgets** (“don’t spend more than $5”) | Free | Not enforceable. The retry loop does not read the prompt. |

The gap is narrow on purpose: **portable, on-chain, x402-native spend policy on Solana.** If we describe ourselves as “the agent wallet,” we lose to Crossmint. If we describe ourselves as “the thing `wrapFetchWithPayment` should have been,” we have a hackathon demo and a reason a Solana team would merge it.

---

### Why this can ship in a hackathon

- One program, one TAP instruction path (`spend`), one client wrapper around code that already exists in the Kora x402 demo.
- USDC mint + public RPC + Kora local demo = no partners required to show a rejected 4th micropayment.
- No token, no bootstrap marketplace, no need for 150k merchants. One protected endpoint is enough to prove the control.

### Risks we are not hiding

- If Coinbase/Crossmint expose a standard “session spend” that every x402 client honors, Envelope’s policy layer gets absorbed. That’s fine; the program can become the Solana reference implementation.
- Allowlists need facilitator pay-to addresses, which change. Operator UX has to pull them from `/supported`, not from a wiki.
- A malicious agent can still *not work* (refuse to use the shim). That’s acceptable: the USDC is in the PDA. The failure mode is “agent is useless,” not “treasury is gone.”

### Ask of judges

This is a Colosseum build, not a vision deck. The artifact is: a funded Envelope, a 402 call that pays through it, and a 402 call that is rejected when the cap is hit — all on Solana USDC, all without the agent holding the funds.
