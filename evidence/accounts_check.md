# Accounts live check

- **signup: pass** — Both teachers signed up through the UI.
- **wizard: pass** — Setup wizard skip persisted.
- **roll: pass** — Both rolls saved: 10 Low / 16 Mid / 12 High; roll 2 is Bhavya (Mid).
- **plans (fake): pass** — Two deterministic FunctionModel-equivalent lesson fixtures created; no real calls made.
- **ownership: pass** — Both directions returned 404 and class lists were isolated.
- **relogin: pass** — A logged out, logged back in, and retained class, roll, and lesson.
- **reset: pass** — Reset link, new password and old-password rejection passed.
- **reload: pass** — App remained visible after reload.
- **demo: pass** — Demo login completed and app is visible.
- **admin: pass** — Admin listed 3 teachers and CSV downloaded.
- **screenshots: pass** — Auth screenshots saved.
