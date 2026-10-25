from pathlib import Path

import pytest

from app.roll import parse_roll_file


FIXTURES = Path(__file__).parent / 'fixtures' / 'class_roll'


@pytest.mark.parametrize('filename', ['class_roll_3A_valid.csv', 'class_roll_3A_valid.xlsx'])
def test_valid_roll_fixtures_have_expected_levels(filename):
    path = FIXTURES / filename
    parsed = parse_roll_file(path.read_bytes(), path.name)
    assert len(parsed) == 38
    assert all(row['valid'] for row in parsed)
    assert {level: sum(row['readiness_level'] == level for row in parsed)
            for level in ('low', 'mid', 'high')} == {'low': 10, 'mid': 16, 'high': 12}


@pytest.mark.parametrize('filename', ['class_roll_messy.csv', 'class_roll_messy.xlsx'])
def test_messy_roll_fixtures_flag_rows_without_guessing(filename):
    path = FIXTURES / filename
    parsed = parse_roll_file(path.read_bytes(), path.name)
    assert [row['roll_no'] for row in parsed if row['valid']] == [1, 2, 3, 4, 5, 8, 10]
    flagged = {row['roll_no']: row['errors'] for row in parsed if not row['valid']}
    assert set(flagged) == {6, 7, 9}
    assert flagged[6] == ['readiness level is blank']
    assert flagged[7] == ['unknown readiness level: Medium']
    assert flagged[9] == ['name is missing']
    assert parsed[8]['readiness_level'] == 'high'
