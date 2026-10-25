from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

class IdParser(HTMLParser):
    def __init__(self): super().__init__(); self.values=[]
    def handle_starttag(self, tag, attrs):
        attrs=dict(attrs)
        for key in ('id','data-testid'):
            if attrs.get(key): self.values.append((key, attrs[key]))

def test_static_auth_ids_are_unique():
    parser=IdParser(); parser.feed((Path('static/index.html')).read_text())
    duplicates=[key for key,count in Counter(parser.values).items() if count > 1]
    assert not duplicates, duplicates
