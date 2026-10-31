"""Evidence-led narrative, openly licensed topic photography, and relevant verified data."""
import re
import requests

# Broad, auditable metric library; charts are only shown for a question-relevant match.
METRICS={
 "employment":("SL.UEM.TOTL.ZS","Unemployment rate","% of labor force"),
 "unemployment":("SL.UEM.TOTL.ZS","Unemployment rate","% of labor force"),
 "internet":("IT.NET.USER.ZS","Individuals using the internet","% of population"),
 "digital":("IT.NET.USER.ZS","Individuals using the internet","% of population"),
 "technology":("IT.NET.USER.ZS","Individuals using the internet","% of population"),
 "developer":("IT.NET.USER.ZS","Internet use (technology context)","% of population"),
 "inflation":("FP.CPI.TOTL.ZG","Consumer price inflation","Annual %"),
 "cost of living":("FP.CPI.TOTL.ZG","Inflation (not actual living costs)","Annual %"),
 "economy":("NY.GDP.MKTP.KD.ZG","Real GDP growth","Annual %"),
 "gdp":("NY.GDP.MKTP.KD.ZG","Real GDP growth","Annual %"),
 "business":("IC.BUS.EASE.XQ","Ease of doing business (historical)","Index"),
 "tourism":("ST.INT.ARVL","International tourism arrivals","Arrivals"),
 "travel":("ST.INT.ARVL","International tourism arrivals","Arrivals"),
 "population":("SP.POP.TOTL","Population","People"),
 "health":("SP.DYN.LE00.IN","Life expectancy at birth","Years"),
 "education":("SE.SEC.ENRR","Secondary school enrollment","% gross"),
 "electricity":("EG.ELC.ACCS.ZS","Access to electricity","% of population"),
 "emissions":("EN.GHG.CO2.MT.CE.AR5","CO₂ emissions","Million tonnes"),
}
COUNTRIES={"iceland":"ISL","india":"IND","united states":"USA","usa":"USA","uk":"GBR","united kingdom":"GBR","canada":"CAN","germany":"DEU","france":"FRA","australia":"AUS","japan":"JPN","singapore":"SGP","norway":"NOR","sweden":"SWE","denmark":"DNK","finland":"FIN","brazil":"BRA","china":"CHN","mexico":"MEX","south africa":"ZAF"}
def indicators_for(question,limit=2):
    q=question.lower()
    country=next(((name,code) for name,code in sorted(COUNTRIES.items(),key=lambda x:-len(x[0])) if re.search(r"\b"+re.escape(name)+r"\b",q)),None)
    if not country:return []
    choices=[];used=set()
    for keyword,(code,title,unit) in sorted(METRICS.items(),key=lambda x:-len(x[0])):
        if re.search(r"\b"+re.escape(keyword)+r"\b",q) and code not in used:
            used.add(code);choices.append((code,title,unit))
        if len(choices)>=limit:break
    results=[]
    for code,title,unit in choices:
        try:
            url=f"https://api.worldbank.org/v2/country/{country[1]}/indicator/{code}"
            response=requests.get(url,params={"format":"json","per_page":100},timeout=9)
            response.raise_for_status()
            data=response.json()
            rows=sorted([{"Year":int(v["date"]),"Value":float(v["value"])} for v in data[1] if v.get("value") is not None],key=lambda v:v["Year"])[-20:]
            if len(rows)<4:continue
            results.append({"title":title+" — "+country[0].title(),"unit":unit,"rows":rows,"source":f"https://data.worldbank.org/indicator/{code}?locations={country[1]}","note":"This is a related macro indicator, not a direct measurement of the full research question."})
        except (requests.RequestException,ValueError,TypeError,KeyError,IndexError):continue
    return results

def photographs(question,limit=3):
    """Wikimedia Commons files with thumbnail and attribution; skip unsupported or ambiguous licenses."""
    terms=[w for w in re.findall(r"[a-zA-Z]{4,}",question.lower()) if w not in {"what","tell","about","more","living","how","would","could","should","with","your","there","this","that"}]
    query=" ".join(terms[:5]) or question[:80]
    try:
        response=requests.get("https://commons.wikimedia.org/w/api.php",params={
            "action":"query","generator":"search","gsrsearch":"filetype:bitmap "+query,
            "gsrnamespace":6,"gsrlimit":12,"prop":"imageinfo","iiprop":"url|extmetadata",
            "iiurlwidth":1000,"format":"json"},headers={"User-Agent":"InsightFlowResearch/1.0 (educational analytics app)"},timeout=12)
        response.raise_for_status()
        pages=response.json().get("query",{}).get("pages",{})
        output=[]
        for page in pages.values():
            info=(page.get("imageinfo") or [{}])[0]
            metadata=info.get("extmetadata") or {}
            license_name=re.sub("<[^>]+>","",metadata.get("LicenseShortName",{}).get("value",""))
            if not (license_name.startswith("CC ") or license_name in ("Public domain","CC0")):continue
            thumb=info.get("thumburl")
            original=info.get("descriptionurl")
            if thumb and original and thumb.startswith("https://"):
                output.append({"url":thumb,"page":original,"title":page.get("title","").replace("File:",""),"license":license_name})
            if len(output)>=limit:break
        return output
    except (requests.RequestException,ValueError,TypeError):return []

def narrative(question,report):
    """Presentation structure from evidence; never invent a conclusion."""
    findings=report.get("findings",[])
    if not findings:return []
    chapters=[]
    for index,finding in enumerate(findings[:6]):
        text=finding.get("text","").strip()
        if not text:continue
        chapters.append({"label":f"Chapter {index+1:02d}","title":finding.get("heading","Research evidence"),
                         "body":text,"source":finding.get("source","")})
    return chapters
