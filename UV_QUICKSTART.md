# uv Quick Start for Reel Summarizer

## TL;DR - 3 Steps

### 1️⃣ Install uv
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2️⃣ Setup project
```bash
cd reel-summarizer
uv sync
cp .env.example .env
# Edit .env with your API keys
```

### 3️⃣ Run it!
```bash
uv run reel_summarizer.py "https://www.instagram.com/reel/ABC123xyz/"
```

---

## Installation by OS

### macOS
```bash
# Option 1: Using install script
curl -LsSf https://astral.sh/uv/install.sh | sh

# Option 2: Using Homebrew
brew install uv

# Verify
uv --version
```

### Linux
```bash
# Using install script
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with apt (Debian/Ubuntu)
sudo apt-get update && sudo apt-get install -y uv

# Verify
uv --version
```

### Windows (PowerShell)
```powershell
powershell -ExecutionPolicy BypassUser -c "irm https://astral.sh/uv/install.ps1 | iex"

# Verify
uv --version
```

---

## First Time Setup

```bash
# Navigate to project
cd path/to/reel-summarizer

# Install dependencies (creates virtual environment)
uv sync

# Copy environment template
cp .env.example .env

# Edit with your API keys
# On macOS/Linux
nano .env

# On Windows
notepad .env
```

---

## Running the Script

```bash
# Simplest way (with uv)
uv run reel_summarizer.py "URL_HERE"

# Or without uv (if dependencies installed)
python reel_summarizer.py "URL_HERE"
```

### Examples
```bash
uv run reel_summarizer.py "https://www.instagram.com/reel/ABC123xyz/"
uv run reel_summarizer.py "https://www.instagram.com/p/XYZ789abc/"
```

---

## 💰 Free Models (No Cost!)

The script **defaults to free Mistral 7B model**. No payment needed!

```bash
# In .env (optional - this is the default)
OPENROUTER_MODEL=mistralai/mistral-7b-instruct
```

Other free options:
```bash
OPENROUTER_MODEL=meta-llama/llama-2-7b-chat
OPENROUTER_MODEL=nous-hermes-2-mixtral-8x7b-dpo
```

See `.env.example` for complete list and comparisons.

---

## Common Commands

```bash
# Install/sync dependencies
uv sync

# Run script
uv run reel_summarizer.py "url"

# Get Python shell with dependencies
uv run python

# Update lock file
uv lock --upgrade

# See what's installed
uv pip list

# Add new package
uv pip install package-name

# Remove package
uv pip uninstall package-name

# Check Python version
uv python --version
```

---

## File Locations

```
your-project/
├── reel_summarizer.py          # Main script
├── pyproject.toml              # uv configuration
├── uv.lock                     # Dependencies lock file (auto-created)
├── requirements.txt            # Fallback for pip
├── .env                        # Your API keys (DON'T commit!)
├── .env.example               # Template
└── UV_QUICKSTART.md           # Quick start guide
```

---

## Troubleshooting

### uv not found after install
Add to your shell profile:
```bash
export PATH="$HOME/.cargo/bin:$PATH"
```

Then restart terminal or run:
```bash
source ~/.bashrc  # or ~/.zshrc for macOS
```

### Module import errors
```bash
# Reinstall dependencies
uv sync --refresh
```

### Wrong Python version
```bash
# Use specific Python version
uv venv --python 3.11
uv sync
```

---

## Why uv is Better

| Feature | pip | uv |
|---------|-----|-----|
| Speed | Slow | ⚡⚡⚡ 50-100x faster |
| Lock file | ❌ | ✅ `uv.lock` |
| Dependency solving | Slow | ⚡ Instant |
| Installation | Slow | ⚡ Instant |
| Python agnostic | ❌ | ✅ |
| Configuration | Complex | Simple |

---

## Next Steps

1. ✅ Install uv
2. ✅ Run `uv sync`
3. ✅ Create `.env` with your API keys
4. ✅ Run `uv run reel_summarizer.py "your-url"`
5. 🎉 Done!

See `README.md` for detailed docs and advanced usage.