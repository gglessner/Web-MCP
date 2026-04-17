# Test fixtures

`target_app.py` is a **deliberately vulnerable** Flask app used by integration tests.
Do not deploy it. Do not use it outside `tests/integration/`.

It provides:
- `GET /echo?q=...` — JSON echo
- `GET /search?q=...` — reflected XSS (unescaped)
- `POST /login` — hardcoded creds `admin`/`hunter2`

Run standalone for manual exploration:
```bash
python tests/fixtures/target_app.py
# Browse to http://127.0.0.1:5055/search?q=<script>alert(1)</script>
```
