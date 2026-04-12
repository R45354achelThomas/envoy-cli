# envoy-cli

> A CLI tool for managing and validating `.env` files across multiple environments with secret diffing support.

---

## Installation

```bash
pip install envoy-cli
```

Or with [pipx](https://pypa.github.io/pipx/) (recommended):

```bash
pipx install envoy-cli
```

---

## Usage

```bash
# Validate a .env file against a schema
envoy validate --file .env --schema .env.schema

# Diff secrets between two environments
envoy diff --base .env.staging --target .env.production

# Sync missing keys from one env file to another
envoy sync --source .env.example --target .env.local

# List all keys in a .env file
envoy list --file .env
```

### Example Output

```
$ envoy diff --base .env.staging --target .env.production

  Missing in production:
    - STRIPE_WEBHOOK_SECRET
    - REDIS_URL

  Extra in production:
    + NEW_RELIC_LICENSE_KEY
```

---

## Features

- ✅ Validate `.env` files against a required key schema
- 🔍 Diff secrets across environments without exposing values
- 🔄 Sync missing keys between env files
- 🔒 Never prints secret values — keys only

---

## License

[MIT](LICENSE) © 2024 envoy-cli contributors