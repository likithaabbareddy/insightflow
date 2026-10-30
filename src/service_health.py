"""Opt-in, redacted API connectivity diagnostics for Streamlit."""
import requests
from src.web_agent import _secret

def check_services():
    result={}
    tavily=_secret("TAVILY_API_KEY")
    if not tavily:result["Tavily"]=("Not configured","Add TAVILY_API_KEY in Streamlit Secrets.")
    else:
        try:
            r=requests.post("https://api.tavily.com/search",json={"api_key":tavily,"query":"official statistics Iceland","max_results":1},timeout=12)
            if r.ok:result["Tavily"]=("Connected","Search endpoint returned successfully.")
            elif r.status_code in (401,403):result["Tavily"]=("Authentication failed","Check your Tavily key and account access.")
            elif r.status_code==429:result["Tavily"]=("Quota or rate limit","Check Tavily usage and plan.")
            else:result["Tavily"]=("API error",f"HTTP {r.status_code}; see server logs for details.")
        except requests.RequestException:result["Tavily"]=("Network error","Search endpoint could not be reached.")
    key=_secret("OPENAI_API_KEY")
    if not key:result["OpenAI"]=("Not configured","Add OPENAI_API_KEY in Streamlit Secrets.")
    else:
        try:
            r=requests.get("https://api.openai.com/v1/models",headers={"Authorization":"Bearer "+key},timeout=12)
            if r.ok:result["OpenAI"]=("Connected","Authentication succeeded; model access and billing still require a live generation test.")
            elif r.status_code==401:result["OpenAI"]=("Authentication failed","Check your OpenAI key.")
            elif r.status_code==429:result["OpenAI"]=("Quota or rate limit","Check billing and usage limits.")
            else:result["OpenAI"]=("API error",f"HTTP {r.status_code}; check project permissions.")
        except requests.RequestException:result["OpenAI"]=("Network error","OpenAI endpoint could not be reached.")
    return result

def show_health():
    import streamlit as st
    with st.expander("🩺 Connection diagnostics",expanded=False):
        st.caption("Run a live connectivity test. This makes one small search request and one API authentication request. Keys are never displayed.")
        if st.button("Check API connections",key="insightflow_health_check"):
            with st.spinner("Checking connections…"):
                for provider,(status,detail) in check_services().items():
                    if status=="Connected":st.success(f"{provider}: {status} — {detail}")
                    else:st.warning(f"{provider}: {status} — {detail}")
