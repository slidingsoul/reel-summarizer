# Instagram Reel Summarizer CLI (Python + uv)

A Python CLI tool that fetches Instagram reel transcripts, summarizes them with any OpenAI-compatible LLM API, and saves the results to Notion.

## Features

✨ Fetch transcripts from Instagram reels using SocialKit API (with Supadata fallback on quota exhaustion)  
🤖 Summarize transcripts with any OpenAI-compatible LLM (OpenRouter, OpenAI, Ollama, ...)  
📝 Automatically save summaries to your Notion database  
📦 Batch mode — pass a file with one URL per line  
🔄 End-to-end automation from reel to Notion  

## Prerequisites

- **Python 3.10+** installed
- **uv** - Fast Python package manager (install from https://docs.astral.sh/uv/getting-started/)
- Active accounts and API keys for:
  - [SocialKit](https://www.socialkit.dev) (primary Instagram transcript extraction)
  - [Supadata](https://dash.supadata.ai) (fallback transcription, used only when SocialKit quota/credits are exhausted)
  - Any OpenAI-compatible LLM API (for AI summarization — e.g. [OpenRouter](https://openrouter.ai), OpenAI, or local Ollama/LM Studio)
  - [Notion](https://www.notion.com) (for saving results)

## Quick Setup with uv

### 1. Install uv

**macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy BypassUser -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Or with Homebrew (macOS/Linux):**
```bash
brew install uv
```

**Verify installation:**
```bash
uv --version
```

### 2. Install Project Dependencies

```bash
# Using uv (recommended - much faster!)
uv sync
```

That's it! `uv sync` handles everything: it creates `.venv`, installs all dependencies from `pyproject.toml`, and installs the `reel-summarizer` command.

### 3. Get API Keys

#### SocialKit API Key
1. Visit [SocialKit](https://www.socialkit.dev)
2. Sign up and go to your dashboard
3. Copy your API key from the API section

#### Supadata API Key (fallback)
1. Visit [Supadata dashboard](https://dash.supadata.ai)
2. Sign up — your API key is generated automatically during onboarding
3. Copy it from the dashboard (see [Supadata docs](https://docs.supadata.ai/))
4. Required: the script validates `SUPADATA_API_KEY` at startup and uses it via the official `supadata` Python SDK (`transcript(url, text=True, mode="auto")`) only when SocialKit reports a quota/credit error (HTTP 402/403/429 or quota message)

#### LLM API Key (any OpenAI-compatible provider)
1. Pick a provider and get an API key (e.g. [OpenRouter](https://openrouter.ai) → Settings → Keys, or [OpenAI](https://platform.openai.com/api-keys))
2. Set `LLM_API_URL` to its chat-completions endpoint, `LLM_API_KEY` to the key, and `LLM_MODEL` to the model name
3. Local servers (Ollama, LM Studio): set `LLM_API_URL` (e.g. `http://localhost:11434/v1/chat/completions`) — any non-empty `LLM_API_KEY` works
4. Legacy `OPENROUTER_API_KEY` / `OPENROUTER_MODEL` are still honored if the `LLM_*` vars are unset

#### Notion API Token
1. Go to [Notion Integrations](https://www.notion.com/my-integrations)
2. Create a new integration
3. Name it (e.g., "Reel Summarizer")
4. Copy the "Internal Integration Token"

#### Notion Page ID
1. Open the Notion parent page where summaries should be created as subpages
2. Look at the URL: `https://notion.so/yourworkspace/abc123def456?v=xyz`
3. The page ID is the part between `/` and `?` (32 characters)
4. Share the page with your integration (page → `...` → Add connections)

### 4. Create .env File

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:
```
SOCIALKIT_API_KEY=sk_xxx...
SUPADATA_API_KEY=supa_xxx...
LLM_API_URL=https://openrouter.ai/api/v1/chat/completions
LLM_API_KEY=sk-or-xxx...
LLM_MODEL=mistralai/mistral-7b-instruct
NOTION_TOKEN=secret_xxx...
NOTION_FOLDER_PAGE_ID=abc123def456789abc123def456789ab
```

**💡 Pro Tip:** `LLM_MODEL` is optional. It defaults to **Mistral 7B (free)** on OpenRouter for summarizing!  
Point `LLM_API_URL` at OpenAI (`https://api.openai.com/v1/chat/completions`) or a local server (e.g. Ollama at `http://localhost:11434/v1/chat/completions`) to switch providers — no code changes needed. Legacy `OPENROUTER_*` vars still work.

## Model Configuration

The script uses **free models by default** on OpenRouter! No additional cost for summarization. Any OpenAI-compatible endpoint works — just change `LLM_API_URL` / `LLM_MODEL`.

### Free Models (Default ✅, OpenRouter)

```bash
# Mistral 7B (default - fastest & free)
LLM_MODEL=mistralai/mistral-7b-instruct

# Llama 2 (free alternative)
LLM_MODEL=meta-llama/llama-2-7b-chat
```

### Paid Models (Better Quality)

```bash
# GPT-4 Turbo (~$0.01-0.03 per request)
LLM_MODEL=openai/gpt-4-turbo-preview

# Claude 3 Opus (~$0.015-0.08 per request)
LLM_MODEL=anthropic/claude-3-opus
```

### Other Providers

```bash
# OpenAI directly
LLM_API_URL=https://api.openai.com/v1/chat/completions
LLM_MODEL=gpt-4o-mini

# Local Ollama (any non-empty LLM_API_KEY works)
LLM_API_URL=http://localhost:11434/v1/chat/completions
LLM_MODEL=llama3.1
```

Just set the vars in your `.env` file and you're good to go!

📖 See `.env.example` for complete list and comparison.

## Usage

### Inside the venv (Recommended)

After `uv sync`, the `reel-summarizer` command is installed into `.venv`:

```bash
source .venv/bin/activate
reel-summarizer "https://www.instagram.com/reel/ABC123xyz/"
```

### With uv (no activation needed)

```bash
# Run the installed command in the project environment
uv run reel-summarizer "https://www.instagram.com/reel/ABC123xyz/"
```

### Standard Python

```bash
# Regular Python execution
python reel_summarizer.py "https://www.instagram.com/reel/ABC123xyz/"
```

> Note: `.env` is loaded from your current directory, so run the command with the project directory as your working directory (the shell function below handles this for you).

### Examples

```bash
# Using full Instagram reel URL
reel-summarizer "https://www.instagram.com/p/ABC123xyz/"

# Works with both /reel/ and /p/ formats
reel-summarizer "https://www.instagram.com/reel/XYZ789abc/"

# Same via uv without activating
uv run reel-summarizer "https://www.instagram.com/reel/XYZ789abc/"

# With environment variable (if .env isn't in current dir)
SOCIALKIT_API_KEY=sk_xxx reel-summarizer "https://www.instagram.com/reel/ABC/"

# Batch file (one URL per line, `#` comments and blanks ignored)
reel-summarizer reels.txt
```

## What Happens

```
Instagram Reel URL 
    ↓
📹 Fetch transcript (SocialKit API)
    ↓ (only on SocialKit quota/credit exhaustion: 402/403/429)
📹 Fallback transcript (Supadata API, mode="auto")
    ↓
🤖 Summarize with AI (LLM)
    ↓
📝 Save to Notion Database
```

The fallback triggers **only** on quota-like SocialKit failures — not on private reels, missing audio, or invalid URLs. Watch the log source tag (`[SocialKit]` vs `[Supadata]`) to see which provider succeeded.

## Output Example

```
🚀 Starting reel summarizer

📹 Fetching transcript from SocialKit...
✅ Transcript fetched successfully [SocialKit]
   Length: 1247 characters

🤖 Sending to LLM for summarization (model: mistralai/mistral-7b-instruct)...
✅ Summarization complete

📝 Creating subpage in Notion...
✅ Subpage created successfully

📌 Page URL: https://notion.so/abc123def456789

🎉 All done!
```

## uv Commands Reference

```bash
# Install dependencies (creates virtual env)
uv sync

# Run the script
uv run reel-summarizer "url-here"

# Run Python REPL with dependencies available
uv run python

# Update dependencies to latest compatible versions
uv lock --upgrade

# Add a new dependency
uv pip install new-package

# Remove a dependency
uv pip uninstall package-name

# Show environment info
uv venv --python 3.11  # Create venv with specific Python version
```

## Why uv?

- ⚡ **50-100x faster** than pip for most operations
- 🔒 **Deterministic** - `uv.lock` file ensures consistent installs
- 🐍 **Python-agnostic** - Works with any Python version
- 📦 **Drop-in pip replacement** - All pip commands work
- 🚀 **Zero configuration** - Works out of the box

## Setup Notion Database (Optional)

Create a database in Notion with these properties:
- **Title** (Text) - Page title
- **Reel URL** (URL) - Link to the Instagram reel
- **Summary** (Text) - AI-generated summary
- **Transcript** (Text) - Full transcript from the reel

Or just use any existing database and the script will create pages automatically.

## Troubleshooting

### "uv: command not found"
Make sure uv is installed:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
# Then add to PATH if needed
export PATH="$HOME/.cargo/bin:$PATH"
```

### "`VIRTUAL_ENV=...` does not match the project environment path"
Your shell has a stale venv activated from before the repo moved. Fix it:
```bash
deactivate 2>/dev/null; unset VIRTUAL_ENV
cd ~/Documents/personal-repos/openrouter-instagram
source .venv/bin/activate
```
If the warning returns in every new terminal, the old path is being re-injected outside your shell configs — check terminal session restore, direnv `.envrc` files, or VS Code's `terminal.integrated.env` / Python interpreter setting. (`uv run --active` forces uv to use the currently active environment instead.)

### "ModuleNotFoundError: No module named 'requests'"
Run dependencies sync:
```bash
uv sync
```

### "Missing required environment variables"
- Ensure your `.env` file exists in the same directory as the script
- Verify all five variables are set (not commented out): `SOCIALKIT_API_KEY`, `SUPADATA_API_KEY`, `LLM_API_KEY` (or legacy `OPENROUTER_API_KEY`), `NOTION_TOKEN`, `NOTION_FOLDER_PAGE_ID`

### "SocialKit API error"
- Check that `SOCIALKIT_API_KEY` is correct
- Verify the Instagram reel URL is public and has audio
- Make sure you have enough credits on SocialKit
- On quota exhaustion (402/403/429) the script automatically falls back to Supadata — check the log for `⚠️ SocialKit quota/credit issue detected`

### "Supadata error"
- `unauthorized` → your `SUPADATA_API_KEY` is invalid; regenerate it at [dash.supadata.ai](https://dash.supadata.ai)
- `limit-exceeded` → Supadata quota/rate limit hit; check usage in the dashboard or response `x-billable-requests` header
- `transcript-unavailable` (HTTP 206) / empty transcript → no speech detected or reel is private/restricted; verify the reel plays in an incognito window
- Long AI-generated transcripts may poll a job for up to ~120s before timing out

### "LLM API error"
- Your `LLM_API_KEY` (or legacy `OPENROUTER_API_KEY`) is invalid or expired
- Regenerate it from [OpenRouter settings](https://openrouter.ai/settings/keys) or your provider's dashboard
- If using a local server, check `LLM_API_URL` is reachable and `LLM_MODEL` is pulled/available

### "Notion API error"
- Verify `NOTION_TOKEN` is correct
- Check that the Notion integration has access to the database
- Ensure `NOTION_FOLDER_PAGE_ID` is exactly 32 characters

### "Invalid URL: Must be an Instagram reel link"
- Use the full URL with `https://`
- Format must be: `https://www.instagram.com/reel/ABC123xyz/`
- Or: `https://www.instagram.com/p/ABC123xyz/`

## Making It a Global Command (Optional)

### Option 1: Shell Function (Recommended, macOS/zsh)

Add to your shell config (`~/.zshrc` for zsh, `~/.bashrc` for bash):

**zsh (`~/.zshrc`):**
```bash
reel-summarizer() {
  cd "$HOME/Documents/personal-repos/openrouter-instagram" && uv run reel-summarizer "$@"
}
```

**bash (`~/.bashrc`):**
```bash
reel-summarizer() {
  cd "$HOME/Documents/personal-repos/openrouter-instagram" && uv run reel-summarizer "$@"
}
```

**Note:** The function `cd`s into the project directory so that `.env` is always found, regardless of your current working directory. `"$@"` passes any arguments through to the script.

Reload your shell config, then:
```bash
source ~/.zshrc    # or: source ~/.bashrc
reel-summarizer "https://www.instagram.com/reel/ABC123xyz/"
```

### Option 2: Wrapper Script

Create `reel-summarizer.sh`:
```bash
#!/bin/bash
cd /path/to/project
uv run reel-summarizer "$@"
```

Then:
```bash
chmod +x reel-summarizer.sh
./reel-summarizer.sh "https://www.instagram.com/reel/ABC123xyz/"
```

## Advanced Usage

### Batch Processing

Create `reels.txt` (one URL per line; blank lines and `#` comments are ignored):
```
https://www.instagram.com/reel/ABC123xyz/
https://www.instagram.com/reel/XYZ789abc/
https://www.instagram.com/p/DEF456uvw/
```

Run batch:
```bash
reel-summarizer reels.txt
```
Each reel is processed in turn; failures are logged per URL without stopping the batch, and a summary (`X succeeded, Y failed`) is printed at the end (exit code 1 if any failed).

### Automation with Cron (macOS/Linux)

```bash
# Edit crontab
crontab -e

# Add this line to run every day at 9 AM
0 9 * * * cd /path/to/project && uv run reel-summarizer "https://www.instagram.com/reel/ABC123xyz/" >> /tmp/reel_summary.log 2>&1
```

## Project Structure

```
.
├── reel_summarizer.py      # Main CLI script
├── pyproject.toml          # Project metadata + dependencies (uv config)
├── uv.lock                 # Lock file (auto-generated)
├── .env.example           # Environment template
└── UV_QUICKSTART.md       # Quick start guide
```

## Cost Considerations

- **SocialKit**: ~1 credit per transcript fetch
- **Supadata** (fallback only): 1 credit per native transcript, 2 credits per minute of AI-generated audio
- **LLM**: Varies by provider/model (~$0.001-0.01 per request with auto/free model on OpenRouter; local Ollama/LM Studio is free)
- **Notion**: Free (but requires existing workspace)

## Security Notes

- Never commit your `.env` file to git
- Add `.env` to your `.gitignore`
- Keep your API keys secret
- Don't share your `.env` file

## Performance Tips

- First call to SocialKit for a new profile might take 5-10 seconds
- Subsequent calls are much faster
- Video URLs from Instagram expire after a few hours
- uv is extremely fast (~10-50ms for most commands)

## License

MIT

## Support

For issues with:
- **uv**: Visit [uv Documentation](https://docs.astral.sh/uv/)
- **SocialKit**: Visit [SocialKit Docs](https://docs.socialkit.dev)
- **Supadata**: Visit [Supadata Docs](https://docs.supadata.ai/)
- **LLM**: Visit [OpenRouter Docs](https://openrouter.ai/docs) (or your provider's docs)
- **Notion**: Visit [Notion API Docs](https://developers.notion.com)