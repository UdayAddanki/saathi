# Full-loop trace

Source: demo account and committed fixtures; no real classroom data.

- **login** — demo session established (0.056s)
- **create class** — Grade 3 Telangana class (0.006s)
- **class roll** — 38 rows saved (0.175s)
- **plan** — Grade 3 place value 5-step lesson (46.57s)
- **print answer sheet** — answer key created for printable sheet (0.018s)
- **upload five sheets** — 5 fixture sheets uploaded (0.017s)
- **read sheets** — batch complete (10.911s)
- **confirm** — 25 results confirmed (0.012s)
- **analysis** — code diagnosis loaded (0.008s)
- **next steps** — Coach output generated (29.362s)
- **worksheet** — worksheet generated (6.651s)
- **use in next lesson** — warm-up saved (0.008s)

## Model calls

| Agent | Input | Cached | Output | Cost | Duration |
|---|---:|---:|---:|---:|---:|
| lesson_planner | 3062 | 1176 | 1975 | $0.001323 | 14125 ms |
| check_builder | 5233 | 2411 | 781 | $0.000974 | 5997 ms |
| reviewer | 6699 | 3147 | 1074 | $0.001286 | 6445 ms |
| lesson_planner_revision | 5010 | 2150 | 2134 | $0.001622 | 13512 ms |
| reviewer_revision | 7003 | 3299 | 920 | $0.001243 | 6446 ms |
| answer_sheet_reader | 1976 | 0 | 94 | $0.000245 | 2219 ms |
| answer_sheet_reader | 1976 | 0 | 94 | $0.000245 | 1910 ms |
| answer_sheet_reader | 1976 | 0 | 94 | $0.000245 | 2038 ms |
| answer_sheet_reader | 1976 | 0 | 169 | $0.000282 | 2651 ms |
| answer_sheet_reader | 1976 | 0 | 94 | $0.000245 | 2049 ms |
| coach | 4509 | 1437 | 1257 | $0.001115 | 12731 ms |
| reviewer | 4332 | 1958 | 371 | $0.000668 | 4797 ms |
| coach_revision | 4656 | 1486 | 1033 | $0.001019 | 11805 ms |
| resource_builder | 2388 | 0 | 755 | $0.000616 | 6626 ms |

## Tools

- lesson_planner: `get_curriculum_context` (0 ms)
- lesson_planner: `get_class_profile` (7 ms)
- lesson_planner: `get_latest_insights` (7 ms)
- check_builder: `get_misconceptions` (0 ms)
- reviewer: `get_curriculum_context` (0 ms)
- lesson_planner_revision: `get_curriculum_context` (0 ms)
- lesson_planner_revision: `get_class_profile` (9 ms)
- lesson_planner_revision: `get_latest_insights` (8 ms)
- reviewer_revision: `get_curriculum_context` (0 ms)
- coach: `get_misconceptions` (0 ms)
- coach: `get_class_profile` (1 ms)
- reviewer: `get_curriculum_context` (0 ms)
- coach_revision: `get_misconceptions` (0 ms)
- coach_revision: `get_class_profile` (1 ms)
