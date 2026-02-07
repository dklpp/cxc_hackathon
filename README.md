# cxc_hackathon

Banking system for customer data and debt tracking.

## Setup

This project uses [uv](https://github.com/astral-sh/uv) for fast Python package management.

### Install uv (if not already installed)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Install dependencies

```bash
uv sync --no-install-project
```

**Note:** This project is a script-based application (not a Python package), so we use `--no-install-project` to skip building/installing the project itself.

This will:
- Create a virtual environment in `.venv/`
- Install all dependencies from `pyproject.toml`
- Generate `uv.lock` for reproducible builds

### Activate the virtual environment

```bash
source .venv/bin/activate
```

Or use `uv run` to run commands directly without activation:

```bash
uv run python DB/db_usage_example.py
```

### Add new dependencies

```bash
uv add package-name
```

### Update dependencies

```bash
uv sync --no-install-project --upgrade
```

## Database Setup

Initialize the database and load sample customers:

```bash
uv run python DB/db_usage_example.py
```

This will create the database tables and load 10 sample customers from `DB/customers/`.