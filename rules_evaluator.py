import csv
from pathlib import Path

RULES_PATH = Path("rules/rome_rules.csv")

def evaluate_rules(facts):
    proposed_articles = []
    
    if not RULES_PATH.exists():
        return proposed_articles
        
    with open(RULES_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            condition = row["condition"]
            
            # Simple safe eval wrapper
            try:
                # Replace '&' with 'and' if necessary, though our CSV has valid Python
                # Evaluate with local dict as facts
                if eval(condition, {"__builtins__": {}}, facts):
                    proposed_articles.append({
                        "instrument": row["instrument"],
                        "article": row["article"],
                        "note": row["note"]
                    })
            except Exception as e:
                # E.g. key missing from facts dict, ignore rule
                pass
                
    return proposed_articles
