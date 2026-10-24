import json
from collections import Counter


def test_every_concept_has_two_to_four_misconceptions():
    concepts = {item['id'] for item in json.load(open('data/concepts.json'))}
    misconceptions = json.load(open('data/misconceptions.json'))
    counts = Counter(item['concept_id'] for item in misconceptions)
    assert concepts - set(counts) == set()
    assert all(2 <= counts[concept_id] <= 4 for concept_id in concepts)


def test_demo_rosters_are_full():
    for item in json.load(open('data/demo_classes.json')):
        assert len(item['students']) == item['class_size']
