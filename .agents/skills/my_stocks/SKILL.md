---
name: my-stocks-patterns
description: Coding patterns and architectural guidelines for the my_stocks project, adapted from Claude Code.
---

# My Stocks Coding Patterns

Follow these guidelines when working on the `my_stocks` project.

## Project Structure
- `src/`: Core logic (data, analysis, decision, communication, backtest, knowledge, utils).
- `config/`: YAML configuration files.
- `docs/`: Markdown requirements and module documentation.
- `tests/`: Pytest test suite.

## Naming Conventions
- **Files**: `snake_case.py`.
- **Classes**: `PascalCase`.
- **Functions/Variables**: `snake_case`.
- **Constants**: `UPPER_SNAKE_CASE`.
- **Private Methods**: `_leading_underscore`.

## Core Patterns
### 1. Configuration (Singleton)
Use `ConfigManager` and the global `get_config()` helper.
```python
from src.utils.config import get_config
config = get_config()
value = config.get("key.path")
```

### 2. Data Loading
Use `KLineDataLoader` or the module-level `load_kline()` helper.
Standard columns: `date`, `open`, `high`, `low`, `close`, `volume`, `amount`.

### 3. Documentation
Use Google-style docstrings with `Args`, `Returns`, and `Raises`.

## Workflows
- **New Modules**: Create directory in `src/`, add `__init__.py`, update `docs/`.
- **New Data Sources**: Implement in `src/data/`, update `config/config.yaml`.
- **Testing**: Use `pytest`, target 80% coverage.
