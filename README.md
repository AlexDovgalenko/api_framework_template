# API-test Framework & Mock Service

A FastAPI micro-service and a Pytest functional suite that can be executed:

- Locally on your workstation
- Against an already-running server
- As an all-in-one Docker container (default)

---

## 📂 Repository Layout

```text
.   
  ├── app/                  # FastAPI demo application (SQLite, JWT, Basic Auth) 
  ├── tests/                # Pytest test-suite + fixtures 
  ├── utils/                # Helper utilities shared by the test framework and mock service
  ├── logging_config.py     # Logging configuration for the test framework 
  ├── requirements.txt      # Python dependencies (app + tests) 
  ├── Dockerfile            # Builds an image that runs app and tests 
  └── README.md             # (this file)
```

---

## Key Capabilities

- Demo API with two auth methods (Bearer & Basic) and SQLite persistence
- Test-framework that:
  - Auto-starts a mock server (Python or Docker)
  - Isolates the DB between tests
  - Runs each test 3× (none / Basic / Bearer auth)
  - Writes a coloured console log and `logs/test_<timestamp>.log`
- Three execution modes controlled by CLI flags (see below)

---

## 🚀 Quick Start
### 1. Run Tests in Docker (default)

Build the image once:

```bash
docker build -t api-tests:latest .
```

Execute the suite (artefacts will be visible on the host):

```bash
mkdir -p logs results
docker run --rm \
  -v "$PWD/logs:/app/logs" \
  -v "$PWD/results:/app/results" \
  api-tests:latest pytest -sv
```

Host artefacts:
```text
logs/test_<YYYY-MM-DD_HH-MM-SS>.log     – test session log file
results/junit.xml                       – CI-friendly test results
results/coverage.xml                    – code-coverage in Cobertura format
```
<hr>

### 2. Run Tests Locally
```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\Activate
pip install -r requirements.txt

pytest --local-run
```
<hr>

### 3. Point the Suite at an External Service

```bash
pytest --source=http://api.dev.company
```
<hr>

## 🔧 Command-line Options

| Flag / Option         | Description                                                      |
|-----------------------|------------------------------------------------------------------|
| `--source=\<URL\>`      | Use an already running API and do not start the demo service     |
| `--local-run`           | Start the demo app via uvicorn subprocess (Python)               |
| `(no flag)`             | Start the demo app inside Docker (demo-tests:latest)             |
| `--log-level=\<LVL\>`   | Console verbosity; file log always keeps INFO+                   |

```text
any other pytest flags e.g: `-q`, `-k smoke`, `-m auth`, `-x`
```
```text
`--source` and `--local-run` are mutually exclusive.
```
<hr>

## 🐳 Dockerfile
- Base image: python:3.11-slim
- Install compiler tools (needed by uvicorn[standard])
- pip install -r requirements.txt (layer-cached)
- Copy project sources into /app

Default command runs:
```bash
pytest -q --junitxml=/app/results/junit.xml --cov=app --cov-report=xml:/app/results/coverage.xml
```

## 🎛️ Customisation

### Change image tag
```bash
export TEST_API_IMAGE=myregistry/demo-tests:ci
docker build -t $TEST_API_IMAGE .
docker run $TEST_API_IMAGE
```

### Add Python packages
Append them to requirements.txt and rebuild the image.

### Pass extra pytest flags
```bash
docker run demo-tests pytest -q -m smoke --log-level=DEBUG
```

## 🩺 Troubleshooting

| Symptom                           | Fix / hint                                                  |
|------------------------------------|-------------------------------------------------------------|
| docker: command not found          | Install Docker Engine or run tests with `--local-run`       |
| Port already in use (local mode)   | Ports are chosen randomly on  re-run                  |
| "docker Python package missing"    | Required only when host pytest spawns containers            |
| Want coloured logs in CI artefacts | ANSI codes are preserved; convert with ansi2html if desired |