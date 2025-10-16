# Running the Labki Packs Tools Test Suite

This document describes how to run all automated tests for **labki-packs-tools** in a clean virtual environment.

---

## 1. Create and activate a virtual environment

From the project root:

### Windows (PowerShell)
```powershell
python -m venv .venv
.venv\Scripts\Activate
```

### MacOS/Linux
```bash
python -m venv .venv
source .venv/bin/activate
```
## 2. Install dependencies

```bash
pdm install -G tests
```

if missing pdm then first run
```bash
pip install pdm
```

## 3. Run tests

```bash
pytest
```
