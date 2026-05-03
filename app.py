import gradio as gr
import re
from rag_answer import answer_question
from rules_evaluator import evaluate_rules

def process_scenario(
    query, 
    is_consumer, 
    trader_targets, 
    is_employment, 
    is_contract, 
    is_tort, 
    no_choice
):
    if not query or not query.strip():
        return (
            "—",
            "—",
            "⚠️ Please enter a scenario description in the query box.",
            ""
        )

    facts = {
        "consumer": bool(is_consumer),
        "trader_targets_consumer_country": bool(trader_targets),
        "employment": bool(is_employment),
        "contract": bool(is_contract),
        "tort": bool(is_tort),
        "no_choice_of_law": bool(no_choice),
    }
    
    proposed_articles = evaluate_rules(facts)
    proposed_text = "None"
    if proposed_articles:
        lines = [f"{a['instrument']}, {a['article']} ({a['note']})" for a in proposed_articles]
        proposed_text = "\n".join(lines)
        
    issues_identified = []
    if is_consumer: issues_identified.append("Consumer Protection")
    if is_employment: issues_identified.append("Employment Law")
    if is_tort: issues_identified.append("Tort / Non-contractual")
    if is_contract: issues_identified.append("Contractual")
    if not issues_identified: issues_identified.append("General / Unknown")
    
    try:
        answer, r_passages, rag_passages, stats = answer_question(query, facts=facts)
    except Exception as e:
        return (
            ", ".join(issues_identified),
            proposed_text,
            "⚠️ Error",
            f"⚠️ Internal error: {e}",
            ""
        )
    
    cites = len(set(re.findall(r'\[\d+\]', answer)))
    dense = stats.get("best_dense", 0.0)
    
    if dense >= 0.70 and cites >= 3:
        badge = "🟢 High"
    elif dense >= 0.60 and cites >= 1:
        badge = "🟡 Medium"
    else:
        badge = "🔴 Low"
        
    conf_text = f"**Confidence:** {badge} <br> <small>(Best Dense: {dense:.2f} | Sources Cited: {cites})</small>"
    
    passages = []
    seen = set()
    for p in r_passages + rag_passages:
        if p["id"] not in seen:
            passages.append(p)
            seen.add(p["id"])
            
    evidence_html = ""
    for i, p in enumerate(passages, start=1):
        score = p.get("score", 1.0)
        # Escape any < > in the text to avoid breaking HTML
        safe_text = p["text"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        evidence_html += (
            f"<details style='margin-bottom:10px;border:1px solid #ccc;padding:6px;border-radius:6px;'>"
            f"<summary style='cursor:pointer;font-weight:bold;'>[{i}] {p['citation']} &nbsp;"
            f"<span style='color:#555;font-size:0.85em;'>(Score: {score:.3f})</span></summary>"
            f"<p style='margin-top:6px;font-size:0.92em;'>{safe_text}</p>"
            f"</details>"
        )
        
    issues_text = ", ".join(issues_identified)
    return issues_text, proposed_text, conf_text, answer, evidence_html


with gr.Blocks(title="Cross-Border Legal RAG") as demo:
    gr.Markdown("# Cross-Border Legal RAG")
    gr.Markdown("**Educational use only — Not legal advice.**")
    
    with gr.Row():
        with gr.Column():
            gr.Markdown("### Scenario Facts")
            query_input = gr.Textbox(lines=4, label="Query", placeholder="Describe the legal scenario...")
            
            with gr.Row():
                is_contract = gr.Checkbox(label="Is Contract?")
                is_tort = gr.Checkbox(label="Is Tort?")
                no_choice = gr.Checkbox(label="No Choice-of-Law Clause?")
            
            with gr.Row():
                is_consumer = gr.Checkbox(label="Consumer Involved?")
                trader_targets = gr.Checkbox(label="Trader Targets Consumer Country?")
                
            with gr.Row():
                is_employment = gr.Checkbox(label="Employment Involved?")
                
            submit_btn = gr.Button("Analyze Scenario", variant="primary")
            
        with gr.Column():
            gr.Markdown("### Analysis")
            out_issues = gr.Textbox(label="Issues Identified", interactive=False)
            out_regimes = gr.Textbox(label="Proposed Regimes & Articles", interactive=False)
            out_confidence = gr.HTML(label="Confidence Level")
            
            gr.Markdown("### Short Memo")
            out_memo = gr.Markdown()
            
            gr.Markdown("### Evidence")
            out_evidence = gr.HTML()
            
    submit_btn.click(
        fn=process_scenario,
        inputs=[
            query_input, 
            is_consumer, 
            trader_targets, 
            is_employment, 
            is_contract, 
            is_tort, 
            no_choice
        ],
        outputs=[out_issues, out_regimes, out_confidence, out_memo, out_evidence]
    )

if __name__ == "__main__":
    import os
    in_space = bool(os.environ.get("SPACE_ID"))
    port = int(os.environ.get("PORT", 7860))
    demo.launch(
        server_name="0.0.0.0",
        server_port=port,
        share=False,
    )
