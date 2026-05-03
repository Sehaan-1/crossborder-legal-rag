import json
import os
from pathlib import Path

scenarios = []

# 10 Consumer scenarios
for i in range(10):
    scenarios.append({
        "facts": {"consumer": True, "trader_targets_consumer_country": True, "no_choice_of_law": True},
        "query": f"A consumer in country A buys from a trader in country B targeting A. Scenario {i}",
        "expected_instruments_articles": ["Rome I (Regulation (EC) No 593/2008), Art. 6(1)"],
        "expect_refusal": False
    })

# 10 Employment scenarios
for i in range(10):
    scenarios.append({
        "facts": {"employment": True, "no_choice_of_law": True},
        "query": f"An employee habitually works in country X but employer is in Y. Scenario {i}",
        "expected_instruments_articles": ["Rome I (Regulation (EC) No 593/2008), Art. 8(2)-(4)"],
        "expect_refusal": False
    })

# 10 Tort scenarios
for i in range(10):
    scenarios.append({
        "facts": {"tort": True},
        "query": f"A traffic accident occurs in country Z between two parties. Scenario {i}",
        "expected_instruments_articles": ["Rome II (Regulation (EC) No 864/2007), Art. 4(1)", "Rome II (Regulation (EC) No 864/2007), Art. 4(2)-(3)"],
        "expect_refusal": False
    })

# 10 Refuse scenarios
refuse_queries = [
    "How do I file tax in France?",
    "Divorce grounds in US?",
    "Jaywalking laws in NY?",
    "Baking a cake?",
    "Penalty for tax evasion?",
    "Building permit in London?",
    "Trademark in Japan?",
    "World cup winner 2022?",
    "Copyright in US?",
    "US work visa requirements?"
]
for q in refuse_queries:
    scenarios.append({
        "facts": {},
        "query": q,
        "expected_instruments_articles": [],
        "expect_refusal": True
    })

os.makedirs("eval", exist_ok=True)
with open("eval/scenarios.jsonl", "w", encoding="utf-8") as f:
    for s in scenarios:
        f.write(json.dumps(s) + "\n")

print(f"Generated {len(scenarios)} scenarios in eval/scenarios.jsonl")
