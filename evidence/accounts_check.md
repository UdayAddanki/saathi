# Accounts live check

Run date: 2026-10-25 15:07:18

- **signup: pass** — Teachers A and B signed up through the UI.
- **roll: pass** — Teacher A saved 10 Low / 16 Mid / 12 High.
- **overall: fail** — APIRequestContext.fetch: Timeout 30000ms exceeded.
Call log:
  - → POST http://127.0.0.1:49485/api/plans
    - user-agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/153.0.8010.12 Safari/537.36
    - accept: */*
    - accept-encoding: gzip,deflate,br
    - content-type: application/json
    - content-length: 142
    - cookie: saathi_session=HLwZwla3s351xECakryqi32NDgTBrvwr_jvojdj9m9Y

