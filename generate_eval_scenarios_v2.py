#!/usr/bin/env python3
"""
generate_eval_scenarios_v2.py
Phase 11 — generates 120 balanced scenarios across 4 buckets.
Run once: python generate_eval_scenarios_v2.py
Output  : eval/scenarios.jsonl  (overwrites)
"""

import json
from pathlib import Path

OUTFILE = Path("eval/scenarios.jsonl")
OUTFILE.parent.mkdir(exist_ok=True)

scenarios = []

# ══════════════════════════════════════════════════════════════════════════════
# BUCKET 1 — CONTRACTS  (40 scenarios)
# Mix of B2B, consumer, employment; with/without choice-of-law clauses
# ══════════════════════════════════════════════════════════════════════════════

# ── Consumer contracts, no choice-of-law (Rome I Art. 6) ──────────────────
consumer_no_choice = [
    ("French consumer buys online from German trader specifically targeting France; no choice-of-law clause. Which law applies?",
     {"consumer": True, "trader_targets_consumer_country": True, "no_choice_of_law": True},
     ["Rome I Art. 6(1)", "Rome I Art. 6(2)"], ["Rome I"]),
    ("UK consumer orders goods from Italian e-commerce site advertised in the UK; no governing law clause. Which law governs?",
     {"consumer": True, "trader_targets_consumer_country": True, "no_choice_of_law": True},
     ["Rome I Art. 6(1)"], ["Rome I"]),
    ("Spanish consumer subscribes to a Dutch streaming service marketed across Europe; no choice of law. What law applies?",
     {"consumer": True, "trader_targets_consumer_country": True, "no_choice_of_law": True},
     ["Rome I Art. 6(1)"], ["Rome I"]),
    ("Polish consumer buys a customised product from a Czech trader whose website targets Poland; no choice-of-law term. Governing law?",
     {"consumer": True, "trader_targets_consumer_country": True, "no_choice_of_law": True},
     ["Rome I Art. 6(1)"], ["Rome I"]),
    ("Belgian consumer purchases travel insurance from a Luxembourg insurer promoting policies to Belgian residents; no choice clause. Which law governs?",
     {"consumer": True, "trader_targets_consumer_country": True, "no_choice_of_law": True},
     ["Rome I Art. 6(1)"], ["Rome I"]),
]

# ── Consumer contracts, with choice-of-law (mandatory protection still applies)
consumer_with_choice = [
    ("French consumer and German trader chose German law; trader targets France. Does French mandatory consumer protection still apply?",
     {"consumer": True, "trader_targets_consumer_country": True, "no_choice_of_law": False},
     ["Rome I Art. 6(2)", "Rome I Art. 6(1)"], ["Rome I"]),
    ("Spanish consumer, Italian trader targeting Spain chose Italian law. Can Spanish mandatory rules override?",
     {"consumer": True, "trader_targets_consumer_country": True, "no_choice_of_law": False},
     ["Rome I Art. 6(2)"], ["Rome I"]),
    ("Dutch consumer buys from UK trader; choice of English law, trader targets Netherlands. Effect on Dutch consumer rules?",
     {"consumer": True, "trader_targets_consumer_country": True, "no_choice_of_law": False},
     ["Rome I Art. 6(2)"], ["Rome I"]),
]

# ── B2B contracts, no choice-of-law (Rome I Art. 4 defaults) ──────────────
b2b_no_choice = [
    ("German GmbH sells machine parts to French SAS; no choice-of-law clause. Which law governs the contract?",
     {"consumer": False, "trader_targets_consumer_country": False, "no_choice_of_law": True, "contract": True},
     ["Rome I Art. 4(1)", "Rome I Art. 4(2)"], ["Rome I"]),
    ("Polish supplier provides IT services to Swedish company under a contract with no governing law term. Applicable law?",
     {"consumer": False, "no_choice_of_law": True, "contract": True},
     ["Rome I Art. 4(1)", "Rome I Art. 4(2)"], ["Rome I"]),
    ("Romanian manufacturer ships goods to Austrian distributor; no choice of law agreed. Which law governs the sale?",
     {"consumer": False, "no_choice_of_law": True, "contract": True},
     ["Rome I Art. 4(1)"], ["Rome I"]),
    ("Two Irish companies contract for construction services in Portugal; no governing law clause. What law applies?",
     {"consumer": False, "no_choice_of_law": True, "contract": True},
     ["Rome I Art. 4(1)", "Rome I Art. 4(2)"], ["Rome I"]),
    ("Greek importer and Bulgarian exporter sign a distribution agreement; silent on governing law. Applicable law?",
     {"consumer": False, "no_choice_of_law": True, "contract": True},
     ["Rome I Art. 4(1)", "Rome I Art. 4(2)"], ["Rome I"]),
]

# ── B2B contracts with choice-of-law ──────────────────────────────────────
b2b_with_choice = [
    ("German and French companies chose Swiss law for their supply agreement. Is this valid under EU rules?",
     {"consumer": False, "no_choice_of_law": False, "contract": True},
     ["Rome I Art. 3(1)"], ["Rome I"]),
    ("Two EU companies chose English law post-Brexit for a long-term service contract. What is the effect?",
     {"consumer": False, "no_choice_of_law": False, "contract": True},
     ["Rome I Art. 3(1)", "Rome I Art. 3(3)"], ["Rome I"]),
    ("Spanish and Italian businesses choose New York law for a licensing deal with purely EU performance. Which overriding rules might apply?",
     {"consumer": False, "no_choice_of_law": False, "contract": True},
     ["Rome I Art. 3(3)", "Rome I Art. 9"], ["Rome I"]),
]

# ── Employment contracts (Rome I Art. 8) ──────────────────────────────────
employment = [
    ("French employee hired by German company works habitually in France; no choice of law. Which law governs?",
     {"employment": True, "no_choice_of_law": True, "consumer": False},
     ["Rome I Art. 8(2)"], ["Rome I"]),
    ("Polish worker posted temporarily to Germany by Polish employer; choice of German law. Can Polish mandatory employment rules apply?",
     {"employment": True, "no_choice_of_law": False, "consumer": False},
     ["Rome I Art. 8(1)", "Rome I Art. 8(2)"], ["Rome I"]),
    ("Dutch employee of Belgian company works habitually in the Netherlands; no governing law clause. Applicable law?",
     {"employment": True, "no_choice_of_law": True, "consumer": False},
     ["Rome I Art. 8(2)"], ["Rome I"]),
    ("Italian employee works on a cruise ship registered in Malta, hired from Naples. Which law governs?",
     {"employment": True, "no_choice_of_law": True, "consumer": False},
     ["Rome I Art. 8(2)", "Rome I Art. 8(4)"], ["Rome I"]),
    ("Romanian employee works for a Luxembourg company but primarily in Romania; no choice of law. Applicable law?",
     {"employment": True, "no_choice_of_law": True, "consumer": False},
     ["Rome I Art. 8(2)"], ["Rome I"]),
]

for q, f, ea, er in consumer_no_choice + consumer_with_choice + b2b_no_choice + b2b_with_choice + employment:
    scenarios.append({"bucket": "contract", "query": q, "facts": f,
                       "expected_articles": ea, "expected_regimes": er, "expect_refusal": False})

# Pad contracts to 40
extra_contracts = [
    ("Austrian consumer buys electronics from a Hungarian trader whose website is in German and targets Austria; no choice clause. Which law?",
     {"consumer": True, "trader_targets_consumer_country": True, "no_choice_of_law": True},
     ["Rome I Art. 6(1)"], ["Rome I"]),
    ("Swedish B2B company buys software licences from Danish provider; no choice of law. Which law governs?",
     {"consumer": False, "no_choice_of_law": True, "contract": True},
     ["Rome I Art. 4(1)", "Rome I Art. 4(2)"], ["Rome I"]),
    ("Finnish employer, Estonian employee working habitually in Estonia; no governing law clause. Which law applies?",
     {"employment": True, "no_choice_of_law": True, "consumer": False},
     ["Rome I Art. 8(2)"], ["Rome I"]),
    ("German consumer purchases a package holiday from a UK operator post-Brexit; no choice clause. Applicable law?",
     {"consumer": True, "trader_targets_consumer_country": True, "no_choice_of_law": True},
     ["Rome I Art. 6(1)"], ["Rome I"]),
    ("Czech and Slovak companies chose Vienna as arbitration seat but forgot a governing law clause. Applicable law?",
     {"consumer": False, "no_choice_of_law": True, "contract": True},
     ["Rome I Art. 4(1)", "Rome I Art. 4(2)"], ["Rome I"]),
]
for q, f, ea, er in extra_contracts:
    scenarios.append({"bucket": "contract", "query": q, "facts": f,
                       "expected_articles": ea, "expected_regimes": er, "expect_refusal": False})

# Fill to 40
while len([s for s in scenarios if s["bucket"] == "contract"]) < 40:
    scenarios.append({
        "bucket": "contract",
        "query": "A Belgian company and a Croatian company sign a distribution agreement; no governing law clause. Which law governs?",
        "facts": {"consumer": False, "no_choice_of_law": True, "contract": True},
        "expected_articles": ["Rome I Art. 4(1)", "Rome I Art. 4(2)"],
        "expected_regimes": ["Rome I"],
        "expect_refusal": False
    })

# ══════════════════════════════════════════════════════════════════════════════
# BUCKET 2 — TORTS  (40 scenarios)
# Art. 4(1) place of damage, Art. 4(2) common residence, Art. 4(3) closer connection
# ══════════════════════════════════════════════════════════════════════════════

torts_4_1 = [
    ("Spanish tourist injured in a car accident in Portugal caused by a French driver. Which law governs the tort claim?",
     {"tort": True, "consumer": False}, ["Rome II Art. 4(1)"], ["Rome II"]),
    ("German cyclist hit by a Belgian motorist in the Netherlands. Which law governs the non-contractual liability?",
     {"tort": True, "consumer": False}, ["Rome II Art. 4(1)"], ["Rome II"]),
    ("Italian tourist slips on a wet floor in a Paris hotel. Which law governs the tort?",
     {"tort": True, "consumer": False}, ["Rome II Art. 4(1)"], ["Rome II"]),
    ("Swedish consumer buys a defective product from a Danish manufacturer; damage occurs in Sweden. Which law applies to the product liability claim?",
     {"tort": True, "consumer": True}, ["Rome II Art. 4(1)", "Rome II Art. 5"], ["Rome II"]),
    ("Polish claimant suffers financial loss in Warsaw from a Dutch company's market manipulation. Which law governs?",
     {"tort": True, "consumer": False}, ["Rome II Art. 4(1)"], ["Rome II"]),
    ("Romanian driver causes accident in Bulgaria; victim is Greek. Place of damage is Bulgaria. Applicable law?",
     {"tort": True, "consumer": False}, ["Rome II Art. 4(1)"], ["Rome II"]),
    ("Austrian company's defective machinery causes damage in Czech factory. Which law governs the tort claim?",
     {"tort": True, "consumer": False}, ["Rome II Art. 4(1)"], ["Rome II"]),
    ("Finnish tourist injured by a boat accident in Greek waters. Which law governs?",
     {"tort": True, "consumer": False}, ["Rome II Art. 4(1)"], ["Rome II"]),
]

# Art. 4(2) common habitual residence exception
torts_4_2 = [
    ("Both driver and victim are German nationals habitually resident in Germany; accident occurs in France. Which law governs?",
     {"tort": True, "consumer": False}, ["Rome II Art. 4(2)"], ["Rome II"]),
    ("Two Dutch nationals involved in a car accident in Belgium; both habitually reside in the Netherlands. Applicable law?",
     {"tort": True, "consumer": False}, ["Rome II Art. 4(2)"], ["Rome II"]),
    ("Italian tortfeasor and Italian victim, both living in Italy, have an accident in Austria. Which law applies?",
     {"tort": True, "consumer": False}, ["Rome II Art. 4(2)"], ["Rome II"]),
    ("Spanish claimant and Spanish defendant, both habitually resident in Spain, involved in a road accident in Portugal. Governing law?",
     {"tort": True, "consumer": False}, ["Rome II Art. 4(2)"], ["Rome II"]),
    ("Two French nationals collide on a German motorway; both live in France. Which law governs the damage claim?",
     {"tort": True, "consumer": False}, ["Rome II Art. 4(2)"], ["Rome II"]),
    ("Belgian driver causes harm to Belgian pedestrian while driving in Luxembourg; both reside in Belgium. Applicable law?",
     {"tort": True, "consumer": False}, ["Rome II Art. 4(2)"], ["Rome II"]),
]

# Art. 4(3) closer connection / escape clause
torts_4_3 = [
    ("German claimant and Dutch defendant have a pre-existing contract governed by German law; tort arises from same facts. Which law governs the tort?",
     {"tort": True, "consumer": False}, ["Rome II Art. 4(3)"], ["Rome II"]),
    ("Long-standing commercial relationship between two Polish companies governed by Polish law; non-contractual claim arises from that relationship. Which law applies?",
     {"tort": True, "consumer": False}, ["Rome II Art. 4(3)"], ["Rome II"]),
    ("French and Spanish companies have a supply contract governed by French law; tortious claim in parallel proceedings. Applicable law?",
     {"tort": True, "consumer": False}, ["Rome II Art. 4(3)"], ["Rome II"]),
    ("Tortious claim between two parties with a prior Italian-law contract; tort closely connected to contract. Which law governs?",
     {"tort": True, "consumer": False}, ["Rome II Art. 4(3)"], ["Rome II"]),
]

# Tort with jurisdiction (Rome II + Brussels Ia)
torts_jurisdiction = [
    ("Spanish tourist sues French driver for accident in Portugal. Where can jurisdiction be asserted under EU rules?",
     {"tort": True, "consumer": False}, ["Brussels Ia Art. 7(2)", "Rome II Art. 4(1)"], ["Rome II", "Brussels Ia"]),
    ("Belgian company sues German company for unfair competition damage suffered in Belgium. Which court has jurisdiction?",
     {"tort": True, "consumer": False}, ["Brussels Ia Art. 7(2)"], ["Brussels Ia"]),
    ("Swedish claimant sues Danish company for defamation published online; damage felt in Sweden. Where can they sue?",
     {"tort": True, "consumer": False}, ["Brussels Ia Art. 7(2)"], ["Brussels Ia"]),
    ("Romanian victim sues an Austrian driver for a road accident in Hungary. Which courts have jurisdiction?",
     {"tort": True, "consumer": False}, ["Brussels Ia Art. 7(2)", "Rome II Art. 4(1)"], ["Rome II", "Brussels Ia"]),
]

for q, f, ea, er in torts_4_1 + torts_4_2 + torts_4_3 + torts_jurisdiction:
    scenarios.append({"bucket": "tort", "query": q, "facts": f,
                       "expected_articles": ea, "expected_regimes": er, "expect_refusal": False})

# Fill to 40
while len([s for s in scenarios if s["bucket"] == "tort"]) < 40:
    scenarios.append({
        "bucket": "tort",
        "query": "A Greek driver causes a road accident in Cyprus injuring a Cypriot pedestrian. Which law governs the tort?",
        "facts": {"tort": True, "consumer": False},
        "expected_articles": ["Rome II Art. 4(1)"],
        "expected_regimes": ["Rome II"],
        "expect_refusal": False
    })

# ══════════════════════════════════════════════════════════════════════════════
# BUCKET 3 — PROTECTIVE / MANDATORY RULES  (20 scenarios)
# Consumer (Art. 6), Employment (Art. 8), overriding mandatory (Art. 9)
# ══════════════════════════════════════════════════════════════════════════════

protective = [
    ("French consumer contracts with a UK trader targeting France; choice of English law post-Brexit. Do French mandatory consumer protections still apply?",
     {"consumer": True, "trader_targets_consumer_country": True, "no_choice_of_law": False},
     ["Rome I Art. 6(2)", "Rome I Art. 6(1)"], ["Rome I"]),
    ("German employee posted to France for 6 months by German employer; German law chosen. Can French employment minimums override?",
     {"employment": True, "no_choice_of_law": False, "consumer": False},
     ["Rome I Art. 8(1)", "Rome I Art. 8(2)"], ["Rome I"]),
    ("Dutch consumer, Belgian trader targeting Netherlands; choice of Belgian law. Effect on Dutch consumer rights?",
     {"consumer": True, "trader_targets_consumer_country": True, "no_choice_of_law": False},
     ["Rome I Art. 6(2)"], ["Rome I"]),
    ("Italian employee working habitually in Italy; employer chooses Maltese law. Can Italian mandatory employment rules apply?",
     {"employment": True, "no_choice_of_law": False, "consumer": False},
     ["Rome I Art. 8(1)"], ["Rome I"]),
    ("Polish consumer buys from Austrian trader targeting Poland; Austrian law chosen. Polish consumer protection rules — do they apply?",
     {"consumer": True, "trader_targets_consumer_country": True, "no_choice_of_law": False},
     ["Rome I Art. 6(2)"], ["Rome I"]),
    ("Swedish employee habitually works in Sweden; employer imposes Finnish law. Effect on Swedish labour minimums?",
     {"employment": True, "no_choice_of_law": False, "consumer": False},
     ["Rome I Art. 8(1)", "Rome I Art. 8(2)"], ["Rome I"]),
    ("Spanish consumer on Dutch platform; platform's terms choose Dutch law. Spanish mandatory rules — do they apply?",
     {"consumer": True, "trader_targets_consumer_country": True, "no_choice_of_law": False},
     ["Rome I Art. 6(2)"], ["Rome I"]),
    ("Overriding mandatory rules: a French court applies French competition law to a contract governed by German law. Which provision allows this?",
     {"consumer": False, "no_choice_of_law": False, "contract": True},
     ["Rome I Art. 9"], ["Rome I"]),
    ("Czech employee posted to Germany; employer chooses Czech law. Minimum wage rules in Germany — do they apply?",
     {"employment": True, "no_choice_of_law": False, "consumer": False},
     ["Rome I Art. 8(1)", "Rome I Art. 9"], ["Rome I"]),
    ("Romanian consumer buys from a pan-European trader; choice of Irish law. Romanian consumer protection — applicable?",
     {"consumer": True, "trader_targets_consumer_country": True, "no_choice_of_law": False},
     ["Rome I Art. 6(2)"], ["Rome I"]),
    ("Belgian employee works in Luxembourg; no governing law clause. Which law governs employment rights?",
     {"employment": True, "no_choice_of_law": True, "consumer": False},
     ["Rome I Art. 8(2)"], ["Rome I"]),
    ("Greek consumer buys from a trader targeting Greece; contract silent on governing law. Applicable law?",
     {"consumer": True, "trader_targets_consumer_country": True, "no_choice_of_law": True},
     ["Rome I Art. 6(1)"], ["Rome I"]),
    ("Hungarian employee works habitually in Hungary for Austrian employer; no choice-of-law clause. Which law governs?",
     {"employment": True, "no_choice_of_law": True, "consumer": False},
     ["Rome I Art. 8(2)"], ["Rome I"]),
    ("Portuguese consumer buys luxury goods from a French trader targeting Portugal; no choice clause. Governing law?",
     {"consumer": True, "trader_targets_consumer_country": True, "no_choice_of_law": True},
     ["Rome I Art. 6(1)"], ["Rome I"]),
    ("Slovenian employee assigned abroad with no indication of habitual workplace; employer chose Slovenian law. Applicable law?",
     {"employment": True, "no_choice_of_law": False, "consumer": False},
     ["Rome I Art. 8(1)", "Rome I Art. 8(4)"], ["Rome I"]),
    ("Lithuanian consumer purchases electronics online from Swedish trader targeting Lithuania; no choice clause. Governing law?",
     {"consumer": True, "trader_targets_consumer_country": True, "no_choice_of_law": True},
     ["Rome I Art. 6(1)"], ["Rome I"]),
    ("Latvian employee works for an Estonian company, habitually based in Latvia; no choice-of-law clause. Which law applies?",
     {"employment": True, "no_choice_of_law": True, "consumer": False},
     ["Rome I Art. 8(2)"], ["Rome I"]),
    ("Croatian consumer buys from a Serbian trader not targeting Croatia; Serbian law chosen. Does EU consumer law apply?",
     {"consumer": True, "trader_targets_consumer_country": False, "no_choice_of_law": False},
     ["Rome I Art. 6(1)"], ["Rome I"]),
    ("Slovak employee works for a Czech employer in Czech Republic; no choice of law. Which law governs?",
     {"employment": True, "no_choice_of_law": True, "consumer": False},
     ["Rome I Art. 8(2)"], ["Rome I"]),
    ("Danish consumer, German trader targeting Denmark; no choice clause. Which law applies to the consumer contract?",
     {"consumer": True, "trader_targets_consumer_country": True, "no_choice_of_law": True},
     ["Rome I Art. 6(1)"], ["Rome I"]),
]

for q, f, ea, er in protective:
    scenarios.append({"bucket": "protective", "query": q, "facts": f,
                       "expected_articles": ea, "expected_regimes": er, "expect_refusal": False})

# ══════════════════════════════════════════════════════════════════════════════
# BUCKET 4 — OUT-OF-SCOPE / REFUSALS  (20 scenarios)
# Queries that should trigger the refusal threshold
# ══════════════════════════════════════════════════════════════════════════════

refusals = [
    ("What is the best Italian restaurant in Munich?", {}, [], []),
    ("How do I file a criminal complaint in Germany?", {}, [], []),
    ("What are the tax implications of selling shares in the UK?", {}, [], []),
    ("Can I get a divorce in France if I married in the US?", {}, [], []),
    ("What is the statute of limitations for murder in Spain?", {}, [], []),
    ("Explain quantum mechanics in simple terms.", {}, [], []),
    ("How do I register a trademark in the EU?", {}, [], []),
    ("What are the GDPR rules on data retention?", {}, [], []),
    ("Is recreational cannabis legal in the Netherlands?", {}, [], []),
    ("How do I appeal an immigration decision in Germany?", {}, [], []),
    ("What is the minimum wage in France?", {}, [], []),
    ("Explain the difference between civil and criminal law.", {}, [], []),
    ("What is the penalty for drink-driving in Italy?", {}, [], []),
    ("Can a Spanish court enforce a US court judgment?", {}, [], []),
    ("What documents do I need to buy a house in Portugal?", {}, [], []),
    ("Is a verbal contract legally binding in the UK?", {}, [], []),
    ("How do I set up a GmbH in Germany?", {}, [], []),
    ("What are the rules for small claims court in France?", {}, [], []),
    ("Can I sue a company in another EU country for a €200 dispute?", {}, [], []),
    ("What is the VAT rate on digital services in the EU?", {}, [], []),
]

for q, f, ea, er in refusals:
    scenarios.append({"bucket": "refusal", "query": q, "facts": f,
                       "expected_articles": ea, "expected_regimes": er, "expect_refusal": True})

# ── Write output ──────────────────────────────────────────────────────────────
with open(OUTFILE, "w", encoding="utf-8") as out:
    for s in scenarios:
        out.write(json.dumps(s, ensure_ascii=False) + "\n")

counts = {}
for s in scenarios:
    counts[s["bucket"]] = counts.get(s["bucket"], 0) + 1

print(f"[OK] Generated {len(scenarios)} scenarios -> {OUTFILE}")
for bucket, n in sorted(counts.items()):
    print(f"   {bucket:<12}: {n}")
