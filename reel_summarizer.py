#!/usr/bin/env python3
"""
Instagram Reel Summarizer
Fetches transcripts, summarizes with AI, and saves to Notion.
"""

import sys
import re
import requests
from datetime import datetime
from dotenv import load_dotenv
import os
from notion_client import Client

# Load environment variables
load_dotenv()

SOCIALKIT_API_KEY = os.getenv('SOCIALKIT_API_KEY')
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
NOTION_TOKEN = os.getenv('NOTION_TOKEN')
NOTION_FOLDER_PAGE_ID = os.getenv('NOTION_FOLDER_PAGE_ID')

def validate_env():
    """Validate that all required environment variables are set."""
    missing = []

    if not SOCIALKIT_API_KEY:
        missing.append('SOCIALKIT_API_KEY')
    if not OPENROUTER_API_KEY:
        missing.append('OPENROUTER_API_KEY')
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


def fetch_transcript(reel_url):
    """Fetch transcript from SocialKit API."""
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
        print('✅ Transcript fetched successfully')
        print(f'   Length: {len(transcript)} characters\n')

        return transcript

    except requests.exceptions.Timeout:
        raise Exception('SocialKit API timeout - reel might not have audio or transcript available')
    except requests.exceptions.RequestException as e:
        raise Exception(f'SocialKit API error: {e}')


def summarize_text(transcript):
    """Summarize transcript using OpenRouter API."""
    print('🤖 Sending to OpenRouter for summarization...')

    prompt = f"""Summarize the following Instagram reel transcript using Markdown format.

START with a single line title using # (e.g., # Amazing Title Here)
Then use:
- **Bold** for key points
- Bullet points for key takeaways

{transcript}"""

    url = 'https://openrouter.ai/api/v1/chat/completions'
    headers = {
        'Authorization': f'Bearer {OPENROUTER_API_KEY}',
        'HTTP-Referer': 'https://github.com',
        'X-Title': 'Reel Summarizer CLI',
    }

    # Use model from environment variable or fallback to free model
    model = os.getenv('OPENROUTER_MODEL', 'mistralai/mistral-7b-instruct')

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
            raise Exception(f"OpenRouter error: {data['error'].get('message', 'Unknown error')}")

        summary = data['choices'][0]['message']['content']
        print('✅ Summarization complete\n')

        return summary

    except requests.exceptions.RequestException as e:
        raise Exception(f'OpenRouter API error: {e}')


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


def main():
    """Main function."""
    # Validate environment
    validate_env()

    # Get reel URL from command line
    if len(sys.argv) < 2:
        print('Usage: python reel_summarizer.py <instagram-reel-url>')
        print('\nExample: python reel_summarizer.py https://www.instagram.com/reel/ABC123/')
        sys.exit(1)

    reel_url = sys.argv[1]

    # Validate URL
    try:
        validate_url(reel_url)
    except ValueError as e:
        print(str(e))
        sys.exit(1)

    try:
        print('🚀 Starting reel summarizer\n')

        # Fetch transcript
        transcript = fetch_transcript(reel_url)

        # Summarize
        summary = summarize_text(transcript)

        # Save to Notion
        save_to_notion(summary)

        print('🎉 All done!')

    except Exception as e:
        print(f'\n❌ Process failed: {str(e)}')
        sys.exit(1)


if __name__ == '__main__':
    main()
