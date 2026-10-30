from src.web_agent import _curated_leads, classify

def test_iceland_has_relevant_official_sources():
    leads=_curated_leads('living in Iceland for an IT developer',classify('living in Iceland for an IT developer'))
    assert any('island.is' in lead['url'] for lead in leads)
    assert not any('worldbank' in lead['url'] for lead in leads)

def test_india_business_has_registration_sources():
    leads=_curated_leads('starting an event management business in India', 'business feasibility')
    assert any('mca.gov.in' in lead['url'] for lead in leads)
