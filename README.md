# API-test Framework & Mock Service

A FastAPI micro-service and a Pytest functional suite that can be executed:

- Locally on your workstation
- Against an already-running server
- As an all-in-one Docker container

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
- Test-framework:
  - Auto-starts a mock server locally or withing Docker container
  - Isolates (clean-up) the DB between tests
  - Runs test against (None / Basic / Bearer) Auth methods
  - Writes a coloured console log in `logs/test_<timestamp>.log` logfile
- Three execution modes controlled by CLI flags (see below)

---

## 🚀 Quick Start
### 0. Preconditions

Build the Docker image:

```bash
docker build -t api-tests:latest .
```

Start test FastAPI Mock application at base URL: http://localhost:50001

```bash
uvicorn app.main:app --port=50001
```

### 1. Run Tests in Docker
Run test using 'Detached' mode (works on Linux and MacOS, For Windows, replace $(pwd) with the absolute path of the project directory):

*Start contained in the detached mode*
```bash
docker run --rm -td -v "$(pwd):/tests" -v "$(pwd)/logs:/tests/logs" -v "$(pwd)/results:/tests/results" --name api-tests-container api-tests
```
*Execute tests within running Docker container, starting mock app*
```bash
docker exec api-tests-container -c "python3 -m pytest -sv --log-level=INFO tests/test_users.py::test_create_and_fetch_user"
```

Run tests within docker container 'non-interactive' mode providing target URL of the service started on host machine:

```bash
docker run --rm -v "$(pwd):/tests" -v "$(pwd)/logs:/tests/logs" -v "$(pwd)/results:/tests/results" --name api-tests-container api-tests:latest -c "python3 -m pytest -sv --log-level=DEBUG --source=http://host.docker.internal:50001 tests/test_users.py::test_create_and_fetch_user"
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
```

```bash
python -m pytest -sv --log-level=INFO  tests/test_users.py::test_create_and_fetch_user
```

<hr>

### 3. Point the Suite at an External Service

```bash
python -m pytest -sv --log-level=INFO --source=http://api.dev.company  tests/test_users.py
```
or 
```bash
python -m pytest -sv --log-level=INFO --source=http://localhost:50001 tests/test_users.py
```
<hr>

## 🔧 Command-line Options

| Flag / Option         | Description                                                   |
|-----------------------|---------------------------------------------------------------|
| `--source=<URL>`      | Uses an already running API without start of the demo service |
| `--log-level=\<LVL\>` | Console verbosity; file log always keeps INFO+                |

```text
any other pytest flags e.g: `-q`, `-s`, `-k smoke`, `-m auth`
```

<hr>

## 🐳 Dockerfile
- Base image: python:3.11-slim
- Install compiler tools (needed by uvicorn[standard])
- pip install -r requirements.txt (layer-cached)
- Copy project sources into /app

Run tests with junitxml test results and test coverage report :
```bash
pytest -sv --junitxml=/results/junit.xml --cov=app --cov-report=xml:/results/coverage.xml
```

Run tests with human-readable HTML report : 

```bash
pytest -sv --html=results/test_report.html --self-contained-html
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


## 🩺 Troubleshooting

| Symptom                           | Fix / hint                                                  |
|------------------------------------|-------------------------------------------------------------|
| docker: command not found          | Install Docker Engine and re-run tests with                |
| Port already in use (local mode)   | Ports are chosen randomly on  re-run                        |
| "docker Python package missing"    | Required only when host pytest spawns containers            |
| Want coloured logs in CI artefacts | ANSI codes are preserved; convert with ansi2html if desired |