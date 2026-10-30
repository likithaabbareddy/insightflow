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
