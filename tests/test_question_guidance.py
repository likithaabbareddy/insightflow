from src.question_guidance import guidance
from src.research import match_topic

def test_relocation_question_is_not_an_indicator():
    q = 'tell more about living in Iceland for an IT developer'
    assert match_topic(q) is None
    result = guidance(q)
    assert 'work' in result['title'].lower()
    assert any('Immigration' in heading for heading, _ in result['sections'])

def test_business_question_has_usable_plan():
    result = guidance('starting an event management business in India')
    assert any('Competition' in heading for heading, _ in result['sections'])
