"""Deterministic, evidence-linked free research summary and verified public-data chart."""
import re
import requests

STOP={"about","how","what","where","when","tell","more","living","being","there","with","from","into","that","this","have","does","would","could","should","your","india","iceland"}
def _sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+",text) if len(s.strip())>45]
def summarize(question, intent, evidence):
    terms={w for w in re.findall(r"[a-z]{4,}",question.lower()) if w not in STOP}
    if "iceland" in question.lower():terms|={"iceland","permit","visa","work","employment","salary","housing","rent","tax","healthcare","developer","technology"}
    if "india" in question.lower() and "business" in intent:terms|={"event","business","registration","gst","license","startup","market","customer"}
    ranked=[]
    for e in evidence:
        title=e.get("title","").lower()
        for sentence in _sentences(e.get("excerpt","")):
            words=set(re.findall(r"[a-z]{4,}",sentence.lower()))
            score=len(words&terms)*3+len(set(re.findall(r"[a-z]{4,}",title))&terms)
            if len(sentence)>360:score-=2
            if re.search(r"privacy policy|cookie|subscribe|newsletter|sign in|all of iceland|latest news|browse world|home page",sentence,re.I):score-=8
            if score>=4 and len(sentence)<=500:
                ranked.append((score,e,sentence))
    ranked.sort(key=lambda row:-row[0])
    findings=[];seen=set();domains=set()
    for score,e,sentence in ranked:
        words=set(re.findall(r"[a-z]{4,}",sentence.lower()))
        fingerprint=frozenset(words)
        if any(len(fingerprint&old)/max(1,len(fingerprint|old))>.65 for old in seen):continue
        if e["url"] in domains and len(domains)<3:continue
        findings.append({"heading":e["title"],"text":sentence,"source":e["url"]})
        domains.add(e["url"]);seen.add(fingerprint)
        if len(findings)>=5:break
    if findings:
        summary=f"Found {len(findings)} question-relevant statements in public sources. The highlights below are extracted evidence, not an AI-generated interpretation. Review each cited source before making decisions."
    else:
        summary="Sources were found, but none contained enough question-specific information for a reliable analysis. Try a narrower question."
    return {"summary":summary,"findings":findings}

def public_indicator(question):
    q=question.lower()
    if "iceland" in q and any(x in q for x in ("developer","tech","it ","internet","living","work")):
        country,indicator,label,unit="ISL","IT.NET.USER.ZS","Internet use in Iceland","% of population"
    elif "india" in q and any(x in q for x in ("event","business","market","startup")):
        country,indicator,label,unit="IND","NY.GDP.PCAP.CD","India GDP per capita (market context)","Current US dollars"
    else:return None
    try:
        r=requests.get(f"https://api.worldbank.org/v2/country/{country}/indicator/{indicator}",params={"format":"json","per_page":80},timeout=12)
        r.raise_for_status()
        payload=r.json()
        rows=[{"Year":int(x["date"]),"Value":float(x["value"])} for x in payload[1] if x.get("value") is not None]
        rows=sorted(rows,key=lambda x:x["Year"])[-20:]
        if len(rows)<3:return None
        return {"title":label,"unit":unit,"rows":rows,"source":f"https://data.worldbank.org/indicator/{indicator}?locations={country}","note":"Contextual indicator only: this does not measure software salaries, job openings, cost of living or event-business demand."}
    except (requests.RequestException,ValueError,TypeError,KeyError,IndexError):return None
