#!/usr/bin/env python3
"""
Instagram Reel Summarizer
Fetches transcripts, summarizes with AI, and saves to Notion.
"""

import sys
import re
import time
import requests
from datetime import datetime
from dotenv import load_dotenv
import os
from notion_client import Client

try:
    from supadata import Supadata, SupadataError
except ImportError:  # pragma: no cover - surfaced clearly at runtime
    Supadata = None
    SupadataError = Exception

# Load environment variables
load_dotenv()

SOCIALKIT_API_KEY = os.getenv('SOCIALKIT_API_KEY')
SUPADATA_API_KEY = os.getenv('SUPADATA_API_KEY')
# Canonical LLM settings (provider-agnostic, OpenAI-compatible chat completions).
# OPENROUTER_* are still honored as legacy fallbacks.
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
NOTION_TOKEN = os.getenv('NOTION_TOKEN')
NOTION_FOLDER_PAGE_ID = os.getenv('NOTION_FOLDER_PAGE_ID')

DEFAULT_LLM_API_URL = 'https://openrouter.ai/api/v1/chat/completions'
DEFAULT_LLM_MODEL = 'mistralai/mistral-7b-instruct'


def get_llm_api_url():
    """Resolve the chat-completions endpoint URL (any OpenAI-compatible provider)."""
    return (os.getenv('LLM_API_URL') or DEFAULT_LLM_API_URL).strip() or DEFAULT_LLM_API_URL


def get_llm_api_key():
    """Resolve the LLM API key (LLM_API_KEY preferred, OPENROUTER_API_KEY legacy)."""
    return os.getenv('LLM_API_KEY') or os.getenv('OPENROUTER_API_KEY')


def get_llm_model():
    """Resolve the LLM model name (LLM_MODEL preferred, OPENROUTER_MODEL legacy)."""
    return os.getenv('LLM_MODEL') or os.getenv('OPENROUTER_MODEL') or DEFAULT_LLM_MODEL

def validate_env():
    """Validate that all required environment variables are set."""
    missing = []

    if not SOCIALKIT_API_KEY:
        missing.append('SOCIALKIT_API_KEY')
    if not SUPADATA_API_KEY:
        missing.append('SUPADATA_API_KEY (required for transcription fallback)')
    if not get_llm_api_key():
        missing.append('LLM_API_KEY (or legacy OPENROUTER_API_KEY)')
    if not NOTION_TOKEN:
        missing.append('NOTION_TOKEN')
    if not NOTION_FOLDER_PAGE_ID:
        missing.append('NOTION_FOLDER_PAGE_ID')

    if missing:
        print('❌ Missing required environment variables:')
        for var in missing:
            print(f'   - {var}')
        sys.exit(1)


def validate_url(reel_url):
    """Validate that the URL is a valid Instagram reel link."""
    if 'instagram.com' not in reel_url:
        raise ValueError('❌ Invalid URL: Must be an Instagram reel link')

    if not re.search(r'instagram\.com/(?:p|reel)/', reel_url):
        raise ValueError('❌ Invalid URL: Must be an Instagram reel or post link (formats: /p/ or /reel/)')


def markdown_to_notion_blocks(md_text: str) -> list[dict]:
    """Convert Markdown into official Notion API Block objects."""
    blocks = []
    lines = md_text.splitlines()

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Heading 1
        if stripped.startswith("# "):
            content = stripped[2:].strip().replace('**', '')
            blocks.append({
                "object": "block",
                "type": "heading_1",
                "heading_1": {"rich_text": [{"type": "text", "text": {"content": content}}]}
            })
        # Heading 2
        elif stripped.startswith("## "):
            content = stripped[3:].strip().replace('**', '')
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"type": "text", "text": {"content": content}}]}
            })
        # Heading 3
        elif stripped.startswith("### "):
            content = stripped[4:].strip().replace('**', '')
            blocks.append({
                "object": "block",
                "type": "heading_3",
                "heading_3": {"rich_text": [{"type": "text", "text": {"content": content}}]}
            })
        # Bullet Points
        elif stripped.startswith("- ") or stripped.startswith("* "):
            content = stripped[2:].strip()
            rich_text = format_rich_text(content)
            blocks.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": rich_text}
            })
        # Numbered Lists
        elif re.match(r"^\d+\.\s", stripped):
            content = re.sub(r"^\d+\.\s", "", stripped)
            rich_text = format_rich_text(content)
            blocks.append({
                "object": "block",
                "type": "numbered_list_item",
                "numbered_list_item": {"rich_text": rich_text}
            })
        # Default Paragraph
        else:
            # Skip lines that are just formatting
            if stripped in ['---', '***', '___']:
                continue
            rich_text = format_rich_text(stripped)
            if rich_text:  # Only add if there's actual content
                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": rich_text}
                })

    return blocks


def format_rich_text(text: str) -> list[dict]:
    """Convert text with **bold** markers into Notion rich text."""
    rich_text = []

    # Clean up multiple asterisks
    text = re.sub(r'\*{3,}', '**', text)

    # Split by bold markers
    parts = re.split(r'(\*\*[^*]+\*\*)', text)

    for part in parts:
        if not part:
            continue

        # Bold text
        if part.startswith('**') and part.endswith('**'):
            content = part[2:-2].strip()
            if content:
                rich_text.append({
                    "type": "text",
                    "text": {"content": content},
                    "annotations": {"bold": True}
                })
        # Regular text
        else:
            # Clean up stray asterisks
            content = part.replace('*', '')
            if content:
                rich_text.append({
                    "type": "text",
                    "text": {"content": content}
                })

    return rich_text


def is_socialkit_quota_error(status_code, message):
    """Return True only when a SocialKit failure looks like quota/credit exhaustion.

    Fallback to Supadata must NOT trigger on private reels, missing audio,
    invalid URLs, etc. — only on quota-like signals.
    """
    if status_code in (402, 403, 429):
        return True
    if not message:
        return False
    lowered = str(message).lower()
    quota_markers = (
        'quota', 'credit', 'limit exceeded', 'rate limit', 'too many requests',
        'exhausted', 'insufficient', 'out of credits', 'no credits',
        'payment', 'billing', 'plan', 'upgrade', '402', '429',
    )
    return any(marker in lowered for marker in quota_markers)


def fetch_transcript_socialkit(reel_url):
    """Fetch transcript from SocialKit API (primary provider)."""
    print('📹 Fetching transcript from SocialKit...')

    url = 'https://api.socialkit.dev/instagram/transcript'
    params = {
        'access_key': SOCIALKIT_API_KEY,
        'url': reel_url
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()

        if not data.get('success'):
            raise Exception(f"SocialKit error: {data.get('message', 'Unknown error')}")

        transcript = data['data']['transcript']
        print('✅ Transcript fetched successfully [SocialKit]')
        print(f'   Length: {len(transcript)} characters\n')

        return transcript

    except requests.exceptions.Timeout:
        raise Exception('SocialKit API timeout - reel might not have audio or transcript available')
    except requests.exceptions.RequestException as e:
        status_code = e.response.status_code if getattr(e, 'response', None) is not None else None
        suffix = f' [HTTP {status_code}]' if status_code else ''
        raise Exception(f'SocialKit API error{suffix}: {e}') from e


def _supadata_content_to_text(content):
    """Normalize Supadata transcript content (str or chunk list) to plain text."""
    if content is None:
        return ''
    if isinstance(content, str):
        return content.strip()
    # List of chunks: each may be a dict or TranscriptChunk dataclass
    parts = []
    for chunk in content:
        if isinstance(chunk, dict):
            text = chunk.get('text', '')
        else:
            text = getattr(chunk, 'text', '')
        if text:
            parts.append(str(text).strip())
    return ' '.join(parts).strip()


def _poll_supadata_job(job_id, timeout_s=120, interval_s=2):
    """Poll Supadata transcript job until completed/failed (handles HTTP 202)."""
    url = f'https://api.supadata.ai/v1/transcript/{job_id}'
    headers = {'x-api-key': SUPADATA_API_KEY}
    deadline = time.time() + timeout_s

    while True:
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        status = data.get('status')

        if status == 'completed':
            return _supadata_content_to_text(data.get('content'))
        if status == 'failed':
            raise Exception(f"Supadata job failed: {data.get('error', data)}")
        if time.time() >= deadline:
            raise Exception(f'Supadata job {job_id} timed out after {timeout_s}s (last status: {status})')
        time.sleep(interval_s)


def fetch_transcript_supadata(reel_url):
    """Fetch transcript from Supadata API via official SDK (fallback provider)."""
    if Supadata is None:
        raise Exception('Supadata SDK not installed. Run: uv sync')
    if not SUPADATA_API_KEY:
        raise Exception('Missing SUPADATA_API_KEY - cannot use Supadata fallback')

    print('📹 Fetching transcript from Supadata (fallback)...')

    try:
        client = Supadata(api_key=SUPADATA_API_KEY)
        result = client.transcript(url=reel_url, text=True, mode='auto')

        # Async path: SDK returns BatchJob(job_id=...) for HTTP 202
        job_id = getattr(result, 'job_id', None)
        if job_id:
            print(f'   Supadata job queued ({job_id}), polling for result...')
            transcript = _poll_supadata_job(job_id)
        else:
            transcript = _supadata_content_to_text(getattr(result, 'content', ''))

        if not transcript:
            raise Exception('Supadata returned an empty transcript (no speech detected?)')

        print('✅ Transcript fetched successfully [Supadata]')
        print(f'   Length: {len(transcript)} characters\n')
        return transcript

    except Exception as e:
        # Preserve structured SupadataError details when available
        if SupadataError is not Exception and isinstance(e, SupadataError):
            raise Exception(f'Supadata error [{e.error}]: {e.message} - {e.details}') from e
        if isinstance(e, requests.exceptions.RequestException):
            raise Exception(f'Supadata API error: {e}') from e
        raise


def fetch_transcript(reel_url):
    """Fetch transcript, falling back to Supadata only on SocialKit quota errors."""
    try:
        return fetch_transcript_socialkit(reel_url)
    except Exception as socialkit_error:
        message = str(socialkit_error)
        # Best-effort status extraction for quota detection
        status_code = None
        match = re.search(r'\b(402|403|429)\b', message)
        if match:
            status_code = int(match.group(1))

        if not is_socialkit_quota_error(status_code, message):
            raise

        print(f'⚠️ SocialKit quota/credit issue detected: {message}')
        print('   Falling back to Supadata...\n')
        try:
            return fetch_transcript_supadata(reel_url)
        except Exception as supadata_error:
            raise Exception(
                f'SocialKit quota exhausted and Supadata fallback failed. '
                f'SocialKit: {socialkit_error} | Supadata: {supadata_error}'
            ) from supadata_error


def summarize_text(transcript):
    """Summarize transcript using any OpenAI-compatible chat completions API."""
    model = get_llm_model()
    print(f'🤖 Sending to LLM for summarization (model: {model})...')

    prompt = f"""Summarize the following Instagram reel transcript using Markdown format.

START with a single line title using # (e.g., # Amazing Title Here)
Then use:
- **Bold** for key points
- Bullet points for key takeaways

{transcript}"""

    url = get_llm_api_url()
    api_key = get_llm_api_key()
    if not api_key:
        raise Exception('Missing LLM API key (set LLM_API_KEY or legacy OPENROUTER_API_KEY)')

    headers = {
        'Authorization': f'Bearer {api_key}',
    }
    # OpenRouter-specific headers: only send them to OpenRouter
    if 'openrouter.ai' in url:
        headers.update({
            'HTTP-Referer': 'https://github.com',
            'X-Title': 'Reel Summarizer CLI',
        })

    payload = {
        'model': model,
        'messages': [
            {
                'role': 'user',
                'content': prompt,
            }
        ],
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()

        if 'error' in data:
            raise Exception(f"LLM error: {data['error'].get('message', 'Unknown error')}")

        summary = data['choices'][0]['message']['content']
        print('✅ Summarization complete\n')

        return summary

    except requests.exceptions.RequestException as e:
        raise Exception(f'LLM API error: {e}')


def save_to_notion(summary):
    """Create a subpage under the given parent page with the summary."""
    print('📝 Creating subpage in Notion...')

    notion = Client(auth=NOTION_TOKEN)

    blocks = markdown_to_notion_blocks(summary)

    # Notion API allows up to 100 blocks during initial page creation
    initial_blocks = blocks[:100]
    # Extract title from first line of markdown (# Title)
    lines = summary.split('\n')
    title = lines[0].replace('# ', '').strip() if lines[0].startswith('# ') else f'Reel - {datetime.now().strftime("%Y-%m-%d %H:%M")}'

    try:
        new_page = notion.pages.create(
            parent={"type": "page_id", "page_id": NOTION_FOLDER_PAGE_ID},
            properties={
                "title": [
                    {
                        "type": "text",
                        "text": {"content": title}
                    }
                ]
            },
            children=initial_blocks
        )

        # Append remaining blocks if total blocks > 100
        if len(blocks) > 100:
            page_id = new_page["id"]
            for i in range(100, len(blocks), 100):
                chunk = blocks[i:i + 100]
                notion.blocks.children.append(block_id=page_id, children=chunk)

        print('✅ Subpage created successfully\n')

        page_id = new_page["id"].replace('-', '')
        notion_url = f'https://notion.so/{page_id}'
        print(f'📌 Page URL: {notion_url}')

    except Exception as e:
        raise Exception(f'Notion API error: {str(e)}')


def process_reel(reel_url):
    """Process a single reel URL: fetch transcript, summarize, save to Notion."""
    # Validate URL
    validate_url(reel_url)

    print('🚀 Starting reel summarizer\n')

    # Fetch transcript
    transcript = fetch_transcript(reel_url)

    # Summarize
    summary = summarize_text(transcript)

    # Save to Notion
    save_to_notion(summary)

    print('🎉 All done!')


def read_urls_from_file(file_path):
    """Read reel URLs from a file (one per line, `#` comments and blanks ignored)."""
    urls = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue
            urls.append(stripped)
    return urls


def main():
    """Main function."""
    # Validate environment
    validate_env()

    # Get reel URL or batch file from command line
    if len(sys.argv) < 2:
        print('Usage: reel-summarizer <instagram-reel-url | batch-file>')
        print('\nExamples:')
        print('  reel-summarizer https://www.instagram.com/reel/ABC123/')
        print('  reel-summarizer reels.txt')
        sys.exit(1)

    arg = sys.argv[1]

    # Batch mode: argument is a file with one URL per line
    if os.path.isfile(arg):
        urls = read_urls_from_file(arg)
        if not urls:
            print(f'❌ No URLs found in {arg}')
            sys.exit(1)

        print(f'📦 Batch mode: {len(urls)} URL(s) from {arg}\n')
        succeeded, failed = 0, 0
        for i, reel_url in enumerate(urls, start=1):
            print(f'━━━ [{i}/{len(urls)}] {reel_url} ━━━')
            try:
                process_reel(reel_url)
                succeeded += 1
            except Exception as e:
                failed += 1
                print(f'\n❌ Failed [{i}/{len(urls)}] {reel_url}: {str(e)}\n')

        print(f'\n📊 Batch complete: {succeeded} succeeded, {failed} failed (of {len(urls)})')
        if failed:
            sys.exit(1)
        return

    # Single URL mode
    try:
        process_reel(arg)
    except ValueError as e:
        print(str(e))
        sys.exit(1)
    except Exception as e:
        print(f'\n❌ Process failed: {str(e)}')
        sys.exit(1)


if __name__ == '__main__':
    main()
