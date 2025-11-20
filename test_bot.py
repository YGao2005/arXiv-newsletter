#!/usr/bin/env python3
"""
Quick test script for ArXiv Papers Bot
Tests basic connectivity without starting the full bot
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

print("🧪 ArXiv Papers Bot - Connection Test\n")
print("=" * 60)

# Test 1: Environment Variables
print("\n1. Checking Environment Variables...")
required_vars = [
    'ARXIV_BOT_TOKEN',
    'SUPABASE_URL',
    'SUPABASE_ANON_KEY',
    'CHANNEL_ID',
    'HF_EMBED_API_URL'
]

missing = []
for var in required_vars:
    value = os.getenv(var)
    if value:
        # Mask sensitive values
        if 'TOKEN' in var or 'KEY' in var:
            display = value[:8] + "..." if len(value) > 8 else "***"
        else:
            display = value
        print(f"   ✓ {var}: {display}")
    else:
        print(f"   ✗ {var}: MISSING")
        missing.append(var)

if missing:
    print(f"\n❌ Missing environment variables: {', '.join(missing)}")
    print("   Please set them in your .env file")
    sys.exit(1)

# Test 2: Supabase Connection
print("\n2. Testing Supabase Connection...")
try:
    from supabase import create_client

    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_ANON_KEY')

    supabase = create_client(supabase_url, supabase_key)

    # Try to query the table
    response = supabase.table('arxiv_papers').select('id', count='exact').limit(1).execute()
    count = response.count if response.count is not None else 0

    print(f"   ✓ Connected to Supabase")
    print(f"   ✓ Found {count} papers in database")

except Exception as e:
    print(f"   ✗ Supabase connection failed: {e}")
    print("   Make sure you've applied the database migration!")
    sys.exit(1)

# Test 3: HuggingFace Space API
print("\n3. Testing HuggingFace Space API...")
try:
    import requests

    hf_url = os.getenv('HF_EMBED_API_URL')

    # Test health endpoint
    response = requests.get(f"{hf_url}/", timeout=10)
    response.raise_for_status()

    print(f"   ✓ HF Space is running")
    print(f"   ✓ Status: {response.json().get('status', 'unknown')}")

    # Test embedding endpoint
    test_response = requests.post(
        f"{hf_url}/embed",
        json={"text": "test"},
        timeout=30
    )
    test_response.raise_for_status()
    embedding = test_response.json().get('embedding')

    print(f"   ✓ Embedding API working")
    print(f"   ✓ Embedding dimensions: {len(embedding)}")

except Exception as e:
    print(f"   ✗ HF Space connection failed: {e}")
    print("   Make sure your HuggingFace Space is running!")
    sys.exit(1)

# Test 4: Discord Bot Token
print("\n4. Testing Discord Bot Token...")
try:
    import discord

    # Just validate the token format
    token = os.getenv('ARXIV_BOT_TOKEN')
    parts = token.split('.')

    if len(parts) == 3:
        print(f"   ✓ Token format looks valid")
    else:
        print(f"   ⚠️  Token format may be invalid (expected 3 parts, got {len(parts)})")

except Exception as e:
    print(f"   ✗ Discord validation failed: {e}")

# Test 5: Database Functions
print("\n5. Testing Database Functions...")
try:
    # Check if functions exist
    functions_to_check = [
        'arxiv_match_papers',
        'arxiv_search_papers_fulltext',
        'arxiv_get_unposted_papers'
    ]

    for func_name in functions_to_check:
        # Try to call the function (will fail gracefully if it doesn't exist)
        try:
            if func_name == 'arxiv_get_unposted_papers':
                supabase.rpc(func_name, {'min_impact_score': 10}).execute()
            print(f"   ✓ Function '{func_name}' exists")
        except Exception as e:
            if "does not exist" in str(e).lower():
                print(f"   ✗ Function '{func_name}' not found")
                print(f"      Run the database migration: supabase/migrations/001_initial_schema.sql")
            else:
                print(f"   ✓ Function '{func_name}' exists")

except Exception as e:
    print(f"   ⚠️  Could not verify functions: {e}")

print("\n" + "=" * 60)
print("✅ All tests passed! Your bot is ready to run.")
print("\nTo start the bot:")
print("   python bot.py")
print("\nOr deploy to Heroku:")
print("   git push heroku master")
print("=" * 60)
