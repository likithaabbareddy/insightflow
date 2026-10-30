from src.web_agent import classify, _trusted, _fallback

def test_intent_routing():
    assert classify('Starting an event management business in India','business') == 'business feasibility'
    assert classify('Living in Iceland as an IT developer') == 'relocation and career'

def test_source_allowlist():
    assert _trusted('https://www.gov.in/example')
    assert not _trusted('https://gov.in.evil.example/path')

def test_no_fake_facts_when_sources_missing():
    result = _fallback('Is it feasible?', 'business feasibility', [])
    assert result['findings'] == []
    assert 'No independently' in result['summary']

def test_search_snippets_are_used_without_page_fetch(monkeypatch):
    from src.web_agent import fetch_evidence
    def no_http(*args, **kwargs):
        raise AssertionError("Should not fetch pages when search snippet is present")
    monkeypatch.setattr("src.web_agent.requests.get", no_http)
    sources=[{"title":"Official information","url":"https://island.is/en","excerpt":"A"*200}]
    assert fetch_evidence(sources)[0]["excerpt"]=="A"*200
