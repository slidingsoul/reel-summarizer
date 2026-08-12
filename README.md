# Instagram Reel Summarizer CLI (Python + uv)

A Python CLI tool that fetches Instagram reel transcripts, summarizes them with AI (OpenRouter), and saves the results to Notion.

## Features

✨ Fetch transcripts from Instagram reels using SocialKit API  
🤖 Summarize transcripts with OpenRouter's AI models  
📝 Automatically save summaries to your Notion database  
🔄 End-to-end automation from reel to Notion  

## Prerequisites

- **Python 3.10+** installed
- **uv** - Fast Python package manager (install from https://docs.astral.sh/uv/getting-started/)
- Active accounts and API keys for:
  - [SocialKit](https://www.socialkit.dev) (for Instagram transcript extraction)
  - [OpenRouter](https://openrouter.ai) (for AI summarization)
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

# Or if you prefer pip still
pip install -r requirements.txt
```

That's it! `uv sync` handles everything.

### 3. Get API Keys

#### SocialKit API Key
1. Visit [SocialKit](https://www.socialkit.dev)
2. Sign up and go to your dashboard
3. Copy your API key from the API section

#### OpenRouter API Key
1. Visit [OpenRouter](https://openrouter.ai)
2. Create an account
3. Go to Settings → Keys
4. Create a new API key

#### Notion API Token
1. Go to [Notion Integrations](https://www.notion.com/my-integrations)
2. Create a new integration
3. Name it (e.g., "Reel Summarizer")
4. Copy the "Internal Integration Token"

#### Notion Database ID
1. Open the Notion database where you want to save summaries
2. Look at the URL: `https://notion.so/yourworkspace/abc123def456?v=xyz`
3. The database ID is the part between `/` and `?` (32 characters)

### 4. Create .env File

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:
```
SOCIALKIT_API_KEY=sk_xxx...
OPENROUTER_API_KEY=sk-or-xxx...
OPENROUTER_MODEL=mistralai/mistral-7b-instruct
NOTION_TOKEN=secret_xxx...
NOTION_FOLDER_PAGE_ID=abc123def456789abc123def456789ab
```

**💡 Pro Tip:** The `OPENROUTER_MODEL` is optional. It defaults to **Mistral 7B (free)** for summarizing!  
See `.env.example` for other free models or paid alternatives.

## Model Configuration

The script uses **free models by default**! No additional cost for summarization.

### Free Models (Default ✅)

```bash
# Mistral 7B (default - fastest & free)
OPENROUTER_MODEL=mistralai/mistral-7b-instruct

# Llama 2 (free alternative)
OPENROUTER_MODEL=meta-llama/llama-2-7b-chat
```

### Paid Models (Better Quality)

```bash
# GPT-4 Turbo (~$0.01-0.03 per request)
OPENROUTER_MODEL=openai/gpt-4-turbo-preview

# Claude 3 Opus (~$0.015-0.08 per request)
OPENROUTER_MODEL=anthropic/claude-3-opus
```

Just set `OPENROUTER_MODEL` in your `.env` file and you're good to go!

📖 See `.env.example` for complete list and comparison.

## Usage

### With uv (Recommended)

```bash
# Run directly with uv
uv run reel_summarizer.py "https://www.instagram.com/reel/ABC123xyz/"
```

### Standard Python

```bash
# Regular Python execution
python reel_summarizer.py "https://www.instagram.com/reel/ABC123xyz/"
```

### Examples

```bash
# Using full Instagram reel URL
uv run reel_summarizer.py "https://www.instagram.com/p/ABC123xyz/"

# Works with both /reel/ and /p/ formats
uv run reel_summarizer.py "https://www.instagram.com/reel/XYZ789abc/"

# With environment variable (if .env isn't in current dir)
SOCIALKIT_API_KEY=sk_xxx uv run reel_summarizer.py "https://www.instagram.com/reel/ABC/"
```

## What Happens

```
Instagram Reel URL 
    ↓
📹 Fetch transcript (SocialKit API)
    ↓
🤖 Summarize with AI (OpenRouter)
    ↓
📝 Save to Notion Database
```

## Output Example

```
🚀 Starting reel summarizer

📹 Fetching transcript from SocialKit...
   Length: 1247 characters

✅ Transcript fetched successfully

🤖 Sending to OpenRouter for summarization...
✅ Summarization complete

📝 Saving to Notion...
✅ Saved to Notion successfully

📌 Page URL: https://notion.so/abc123def456789

🎉 All done!
```

## uv Commands Reference

```bash
# Install dependencies (creates virtual env)
uv sync

# Run the script
uv run reel_summarizer.py "url-here"

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

### "ModuleNotFoundError: No module named 'requests'"
Run dependencies sync:
```bash
uv sync
```

### "Missing required environment variables"
- Ensure your `.env` file exists in the same directory as the script
- Verify all four variables are set (not commented out)

### "SocialKit API error"
- Check that `SOCIALKIT_API_KEY` is correct
- Verify the Instagram reel URL is public and has audio
- Make sure you have enough credits on SocialKit

### "OpenRouter API error: 401"
- Your `OPENROUTER_API_KEY` is invalid or expired
- Regenerate it from [OpenRouter settings](https://openrouter.ai/settings/keys)

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
  cd "$HOME/personal-repos/openrouter-instagram" && uv run reel_summarizer.py "$@"
}
```

**bash (`~/.bashrc`):**
```bash
reel-summarizer() {
  cd "$HOME/personal-repos/openrouter-instagram" && uv run reel_summarizer.py "$@"
}
```

**Note:** The function `cd`s into the project directory so that `.env` is always found, regardless of your current working directory. `"$@"` passes any arguments through to the script.

Reload your shell config, then:
```bash
source ~/.zshrc    # or: source ~/.bashrc
reel-summarizer "https://www.instagram.com/reel/ABC123xyz/"
```

### Option 2: Executable Script (macOS/Linux)

```bash
# Make executable
chmod +x reel_summarizer.py

# Create symlink
sudo ln -s "$(pwd)/reel_summarizer.py" /usr/local/bin/reel-summarizer

# Now use it (you'll need uv in your PATH)
reel-summarizer "https://www.instagram.com/reel/ABC123xyz/"
```

### Option 3: Wrapper Script

Create `reel-summarizer.sh`:
```bash
#!/bin/bash
cd /path/to/project
uv run reel_summarizer.py "$@"
```

Then:
```bash
chmod +x reel-summarizer.sh
./reel-summarizer.sh "https://www.instagram.com/reel/ABC123xyz/"
```

## Advanced Usage

### Batch Processing

Create `reels.txt`:
```
https://www.instagram.com/reel/ABC123xyz/
https://www.instagram.com/reel/XYZ789abc/
https://www.instagram.com/p/DEF456uvw/
```

Run batch:
```bash
while IFS= read -r url; do
  uv run reel_summarizer.py "$url"
done < reels.txt
```

### Automation with Cron (macOS/Linux)

```bash
# Edit crontab
crontab -e

# Add this line to run every day at 9 AM
0 9 * * * cd /path/to/project && uv run reel_summarizer.py "https://www.instagram.com/reel/ABC123xyz/" >> /tmp/reel_summary.log 2>&1
```

## Project Structure

```
.
├── reel_summarizer.py      # Main CLI script
├── pyproject.toml          # Project metadata (uv config)
├── uv.lock                 # Lock file (auto-generated)
├── requirements.txt        # Fallback for pip
├── .env.example           # Environment template
└── UV_QUICKSTART.md       # Quick start guide
```

## Cost Considerations

- **SocialKit**: ~1 credit per transcript fetch
- **OpenRouter**: Varies by model (~$0.001-0.01 per request with auto model)
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
- **OpenRouter**: Visit [OpenRouter Docs](https://openrouter.ai/docs)
- **Notion**: Visit [Notion API Docs](https://developers.notion.com)