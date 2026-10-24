from app.curriculum import CONCEPTS, MISCONCEPTIONS, get_curriculum_context
def test_references():
 ids={x['id'] for x in CONCEPTS}; assert all(p in ids for x in CONCEPTS for p in x['prerequisite_ids']); assert all(x['concept_id'] in ids for x in MISCONCEPTIONS)
def test_modes():
 assert get_curriculum_context('TS_SCERT',3,'Mathematics','place value')['mode']=='curated'; assert get_curriculum_context('TS_SCERT',4,'Environmental Studies (EVS)','plants')['mode']=='open'
