"""Human-readable question routing without pretending indicator matches are research answers."""
import re

def guidance(question: str) -> dict:
    q=question.casefold()
    if any(term in q for term in ("living in","move to","moving to","relocat","immigrat","visa","work in","working in")):
        role="software developer / IT professional" if any(t in q for t in ("developer","software"," it ","engineer","programmer")) else "professional"
        return {"title":"Living and working abroad: research guide",
                "intro":f"Your question is about a real-life decision, not a single statistical indicator. Here is a practical investigation for a {role}.",
                "sections":[
                    ("Immigration and work eligibility","Check the destination country's official immigration authority for residence permits, employment permissions, sponsorship rules, processing times and eligibility. Requirements depend on citizenship and circumstances."),
                    ("Job market and compensation","Compare current vacancies for your skills, employers willing to sponsor, salaries by experience, contract terms and local demand. Job listings and salary surveys need dates and citations."),
                    ("Living costs","Build a monthly budget for housing, utilities, groceries, transport, taxes and healthcare. Compare net income with costs; city and household size matter."),
                    ("Quality of life","Research climate, daylight, language, healthcare access, housing availability, community and work-life expectations."),
                    ("Decision checklist","Identify your citizenship, experience, target city, family situation and salary expectations; verify information with official sources before making plans.")],
                "limitations":"This is a research roadmap, not a verified immigration or cost-of-living report. InsightFlow has not retrieved current visa rules, salaries or rents for this question."}
    if any(t in q for t in ("start a business","starting a","business idea","launch a business","open a business","entrepreneur")):
        return {"title":"Business feasibility research guide","intro":"This requires market and regulatory research, not a loosely related economic indicator.",
                "sections":[("Demand and customers","Define your customer segments, service area, purchasing behavior and seasonal demand."),
                            ("Competition","Compare competitors, offerings, pricing and unmet needs."),
                            ("Economics","Estimate startup expenses, unit margins, fixed costs and working capital."),
                            ("Compliance","Verify permits, registrations, tax and insurance requirements with official authorities."),
                            ("Pilot","Test demand with interviews, supplier quotes and a small paid pilot.")],
                "limitations":"This is an investigation plan, not a researched market assessment. No unsupported figures are provided."}
    return {"title":"Research plan for your question","intro":"This question needs sources beyond the currently connected statistical indicators. Rather than show unrelated datasets, here is a transparent next-step plan.",
            "sections":[("Clarify the question","Define the location, timeframe, audience and decision you want to make."),
                        ("Find appropriate evidence","Prioritize official agencies, primary studies and dated specialist sources relevant to the topic."),
                        ("Cross-check claims","Compare independent sources and distinguish facts from interpretation."),
                        ("Build the answer","Summarize findings, uncertainty, practical implications and links to original evidence.")],
            "limitations":"InsightFlow has not yet collected evidence for this question. A broader web-research connector and verified citations are needed for a full answer."}
