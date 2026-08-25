from __future__ import annotations

UPGRADES = {
    "as_of": "2026-08-25",
    "disclaimer": (
        "This section is researched editorial content, not live RPC state. "
        "Dates and statuses were checked against primary Solana Foundation pages "
        "and SIMD text on 2026-08-25. Feature activation can move; treat target "
        "windows as the Foundation's published schedule, not a guarantee."
    ),
    "items": [
        {
            "id": "alpenglow",
            "title": "Alpenglow (SIMD-0326 family)",
            "status": "In development — expected with Agave 4.3 / Q3 2026",
            "headline": "Replace TowerBFT + on-chain votes with Votor; target ~150ms finality.",
            "summary": (
                "Alpenglow is Solana's first major consensus rewrite since TowerBFT. "
                "Phase 1 (Votor) removes Proof of History as a consensus clock and "
                "drops vote transactions from blocks. Validators exchange votes directly; "
                "certificates live in a Pool/Blokstor path instead of as regular txs. "
                "Fast path finalizes a block when ≥80% of stake notarizes in round one; "
                "otherwise a second round can finalize at a 60% stake threshold. "
                "The resilience claim is a 20+20 model: 20% adversarial stake plus 20% "
                "offline stake. Rotor, the later block-propagation replacement for Turbine, "
                "is explicitly out of scope for the first activation."
            ),
            "operator_notes": (
                "BLS pubkey management (SIMD-0387) activated on mainnet 2026-07-08. "
                "Validator Admission Ticket / VAT (SIMD-0357) activated 2026-07-22. "
                "Operators who have not registered a BLS pubkey are excluded from the "
                "VAT-admitted set and stop participating in consensus. VAT gating is not "
                "the same as turning Alpenglow consensus on — that remains a separate "
                "Agave 4.3 activation. VAT is 1.6 SOL per epoch at 400ms slots, scaling "
                "down with SIMD-0525 so daily cost stays ~0.8 SOL."
            ),
            "simds": [
                "SIMD-0326 Alpenglow Consensus Protocol",
                "SIMD-0337 Markers for Alpenglow Fast Leader Handover",
                "SIMD-0357 Alpenglow Validator Admission Ticket",
                "SIMD-0384 Alpenglow Migration",
                "SIMD-0387 BLS Pubkey Management in Vote Account",
            ],
            "sources": [
                {
                    "title": "Solana Upgrades — Alpenglow (Foundation, June 2026; page current as of Aug 2026)",
                    "url": "https://solana.com/upgrades/alpenglow",
                    "dated": "2026-06 / checked 2026-08-25",
                },
                {
                    "title": "Solana Network Upgrades index (Agave 4.3 planned October 2026)",
                    "url": "https://solana.com/news/solana-network-upgrades",
                    "dated": "checked 2026-08-25",
                },
                {
                    "title": "SIMD-0326 Alpenglow proposal",
                    "url": "https://github.com/solana-foundation/solana-improvement-documents/blob/main/proposals/0326-alpenglow.md",
                    "dated": "created 2025-07-25; still the canonical spec in 2026",
                },
            ],
        },
        {
            "id": "simd-0525",
            "title": "SIMD-0525 / SIMD-525 — Reduce Slot Times",
            "status": "Shipped with Agave 4.2 (August 2026); staged feature gates, pending full 200ms",
            "headline": "Cut target slot time from 400ms to 200ms in four 50ms steps.",
            "summary": (
                "PR #525 in the SIMD repo landed as SIMD-0525 on 2026-05-14. The design "
                "keeps ticks_per_slot = 64, leader span = 4 slots, and epoch length = "
                "432,000 slots. Per-slot CU / shred budgets scale down with slot time so "
                "wall-clock throughput does not silently jump. slots_per_year is scaled "
                "up so inflation stays roughly constant in wall-clock terms. Each gate "
                "becomes effective one epoch after activation so Turbine shred limits "
                "stay synchronized. Skip-rate is the published brake: the cluster is not "
                "supposed to take the next 50ms step if skips climb."
            ),
            "operator_notes": (
                "Agave 4.2 shipped August 2026 and is visible on public RPC as solana-core "
                "4.2.0. Official upgrade copy still lists the 200ms end-state as pending "
                "feature activation. Northstar therefore treats SIMD-0525 as a live, "
                "staged rollout and compares measured slot time from "
                "getRecentPerformanceSamples against the 400/350/300/250/200 ms ladder "
                "instead of assuming the final target is already on."
            ),
            "simds": [
                "SIMD-0525 Reduce Slot Times (GitHub PR #525)",
                "Related: SIMD-0357 VAT scaling with slot time",
            ],
            "sources": [
                {
                    "title": "SIMD-0525 Reduce Slot Times (merged 2026-05-14)",
                    "url": "https://github.com/solana-foundation/solana-improvement-documents/blob/main/proposals/0525-reduce-slot-times.md",
                    "dated": "created 2026-05-01, merged 2026-05-14",
                },
                {
                    "title": "Reduced Slot Times upgrade page (updated August 2026)",
                    "url": "https://solana.com/upgrades/reduced-slot-times",
                    "dated": "2026-08",
                },
                {
                    "title": "Solana Network Upgrades — Agave 4.2 shipped August 2026",
                    "url": "https://solana.com/news/solana-network-upgrades",
                    "dated": "checked 2026-08-25",
                },
            ],
        },
        {
            "id": "agave-42-adjacent",
            "title": "Agave 4.2 companions (rent, transaction size)",
            "status": "Client shipped August 2026; feature gates pending/activating",
            "headline": "90% rent reduction (phased) and 4096-byte transactions riding with 4.2.",
            "summary": (
                "The same Agave 4.2 train that carries SIMD-0525 also ships a staged 90% "
                "rent cut (target 696 lamports/byte vs 6,960) and a jump in max transaction "
                "size from 1232 to 4096 bytes. Those changes matter for tokenized assets "
                "and ZK-heavy programs that previously packed against the 1232-byte ceiling."
            ),
            "operator_notes": None,
            "simds": [],
            "sources": [
                {
                    "title": "Solana Network Upgrades — Agave 4.2",
                    "url": "https://solana.com/news/solana-network-upgrades",
                    "dated": "checked 2026-08-25",
                }
            ],
        },
        {
            "id": "agave-41-live",
            "title": "Already live from Agave 4.1 (May 2026)",
            "status": "Live on mainnet",
            "headline": "100M CU blocks, XDP, optimized Token Program, VAT/BLS gates.",
            "summary": (
                "Agave 4.1 raised the block compute limit from 60M to 100M CU, enabled "
                "XDP kernel-bypass networking for block propagation, and shipped a much "
                "cheaper Token Program. Those pieces are the reason a 200ms slot target "
                "is even discussable: replay and networking had to get faster before the "
                "clock could."
            ),
            "operator_notes": None,
            "simds": ["SIMD-0286 / 100M CU blocks context"],
            "sources": [
                {
                    "title": "Solana Network Upgrades — Agave 4.1 shipped May 2026",
                    "url": "https://solana.com/news/solana-network-upgrades",
                    "dated": "checked 2026-08-25",
                }
            ],
        },
    ],
}


def upgrades_payload() -> dict:
    return UPGRADES
