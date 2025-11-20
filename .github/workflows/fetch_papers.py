#!/usr/bin/env python3
"""
ArXiv Paper Fetcher - GitHub Actions Daily Job
Fetches new CS papers from arXiv, generates embeddings, and uses Gemini for analysis
"""

import os
import sys
import json
import time
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import arxiv
import google.generativeai as genai
from supabase import create_client, Client

# Configuration
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
HF_EMBED_API_URL = os.environ.get('HF_EMBED_API_URL')

# Validate environment variables
if not all([SUPABASE_URL, SUPABASE_KEY, GEMINI_API_KEY, HF_EMBED_API_URL]):
    print("❌ Missing required environment variables!")
    print(f"   SUPABASE_URL: {'✓' if SUPABASE_URL else '✗'}")
    print(f"   SUPABASE_KEY: {'✓' if SUPABASE_KEY else '✗'}")
    print(f"   GEMINI_API_KEY: {'✓' if GEMINI_API_KEY else '✗'}")
    print(f"   HF_EMBED_API_URL: {'✓' if HF_EMBED_API_URL else '✗'}")
    sys.exit(1)

# Initialize clients
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel('gemini-2.5-flash-lite')

# Statistics
stats = {
    'fetched': 0,
    'new': 0,
    'duplicates': 0,
    'errors': 0,
    'gemini_calls': 0,
    'embedding_calls': 0
}


def get_embedding(text: str) -> Optional[List[float]]:
    """
    Get embedding from HuggingFace Space API
    """
    try:
        response = requests.post(
            f"{HF_EMBED_API_URL}/embed",
            json={"text": text},
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        stats['embedding_calls'] += 1
        return data['embedding']
    except Exception as e:
        print(f"⚠️  Error getting embedding: {e}")
        return None


def analyze_with_gemini(title: str, abstract: str) -> Optional[Dict]:
    """
    Use Gemini to analyze paper and return structured data
    """
    prompt = f"""You are a HIGHLY CRITICAL reviewer evaluating computer science research papers. Be strict and discriminating in your scoring.

Title: {title}

Abstract: {abstract}

Provide a JSON response with these fields:

1. "score": An integer from 1-10 indicating impact and significance. BE CRITICAL - most papers should score 4-6.

   SCORING RUBRIC (use the FULL range):

   10 = REVOLUTIONARY (e.g., Transformers, ResNet, AlphaGo, GANs when first introduced)
       - Fundamentally changes how we approach a major problem
       - Will be cited 1000+ times and spawn entire research directions
       - Once-in-a-decade breakthrough

   9 = EXCEPTIONAL (major conference best paper caliber)
      - Significant theoretical advance or empirical breakthrough
      - Solves a long-standing important problem
      - Introduces genuinely novel approach with broad applicability

   7-8 = STRONG (top-tier conference accept)
        - Clear novel contribution with solid experimental validation
        - Advances state-of-art meaningfully
        - Well-executed work that others will build upon

   5-6 = SOLID (acceptable conference paper)
        - Incremental but valid contribution
        - Competent execution, some novelty
        - Niche application or modest improvement

   3-4 = WEAK (borderline or reject)
        - Minor variation of existing work
        - Limited novelty or significance
        - Narrow scope or questionable evaluation

   1-2 = POOR (clear reject)
        - No significant contribution
        - Fundamental flaws or already well-known

   DEFAULT ASSUMPTION: Most papers are incremental = 4-6 range. Only score 8+ if you see clear evidence of major impact.

2. "tldr": A single concise sentence (max 150 chars) summarizing the key contribution

3. "tags": An array of 2-5 relevant category tags from this list:
   ["CV", "NLP", "LLM", "Transformers", "Diffusion", "RL", "Robotics", "ML", "Theory", "Systems", "Security", "Other"]

Return ONLY valid JSON in this exact format:
{{"score": <number>, "tldr": "<string>", "tags": [<strings>]}}"""

    try:
        response = gemini_model.generate_content(prompt)
        stats['gemini_calls'] += 1

        # Extract JSON from response
        text = response.text.strip()

        # Try to find JSON in the response
        if '```json' in text:
            text = text.split('```json')[1].split('```')[0].strip()
        elif '```' in text:
            text = text.split('```')[1].split('```')[0].strip()

        # Parse JSON
        data = json.loads(text)

        # Validate structure
        if not all(k in data for k in ['score', 'tldr', 'tags']):
            raise ValueError("Missing required fields in Gemini response")

        # Ensure score is in valid range
        data['score'] = max(1, min(10, int(data['score'])))

        return data

    except Exception as e:
        print(f"⚠️  Error analyzing with Gemini: {e}")
        print(f"   Response: {response.text if 'response' in locals() else 'N/A'}")
        return None


def check_paper_exists(arxiv_id: str) -> bool:
    """
    Check if paper already exists in database
    """
    try:
        result = supabase.table('arxiv_papers').select('arxiv_id').eq('arxiv_id', arxiv_id).execute()
        return len(result.data) > 0
    except Exception as e:
        print(f"⚠️  Error checking if paper exists: {e}")
        return False


def save_paper(paper_data: Dict) -> bool:
    """
    Save paper to Supabase
    """
    try:
        supabase.table('arxiv_papers').insert(paper_data).execute()
        return True
    except Exception as e:
        print(f"❌ Error saving paper: {e}")
        stats['errors'] += 1
        return False


def fetch_arxiv_papers() -> List[arxiv.Result]:
    """
    Fetch papers from arXiv from 2 days ago (yesterday's announcements)

    ArXiv publishes papers at midnight UTC AFTER they are announced.
    - Papers announced on Day N appear in API on Day N+1 at midnight
    - So when this runs at 08:00 UTC, we fetch papers from 2 days ago
    - This gives us "yesterday's announcements" for a true daily newsletter
    """
    # Fetch papers from 2 days ago (the most recent available at 08:00 UTC)
    two_days_ago = datetime.utcnow() - timedelta(days=2)
    two_days_ago_str = two_days_ago.strftime('%Y%m%d')

    print(f"📅 Fetching papers from {two_days_ago_str} (yesterday's announcements)...")

    # Build arXiv query for Computer Science papers from that specific day
    query = f"cat:cs.* AND submittedDate:[{two_days_ago_str}0000 TO {two_days_ago_str}2359]"

    # Search arXiv using the non-deprecated API
    client = arxiv.Client()
    search = arxiv.Search(
        query=query,
        max_results=500,  # ArXiv can have 100-300 CS papers per day
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending
    )

    papers = list(client.results(search))
    stats['fetched'] = len(papers)

    print(f"✓ Fetched {len(papers)} papers from {two_days_ago_str}")

    return papers


def process_papers(papers: List[arxiv.Result]):
    """
    Process each paper: check duplicates, generate embeddings, analyze with Gemini
    """
    print(f"\n🔄 Processing {len(papers)} papers...")

    for i, paper in enumerate(papers, 1):
        try:
            arxiv_id = paper.entry_id.split('/abs/')[-1]

            # Progress indicator
            print(f"\n[{i}/{len(papers)}] Processing: {arxiv_id}")

            # Check if already processed
            if check_paper_exists(arxiv_id):
                print(f"   ⏭️  Already exists, skipping")
                stats['duplicates'] += 1
                continue

            # Prepare text for embedding (abstract only - no need for full paper)
            # We use title + abstract for better semantic search
            embed_text = f"{paper.title}. {paper.summary}"

            # Get embedding (384-dim vector from abstract)
            print(f"   🧠 Generating embedding from abstract...")
            embedding = get_embedding(embed_text)
            if not embedding:
                print(f"   ⚠️  Skipping due to embedding error")
                continue

            # Analyze with Gemini
            print(f"   ✨ Analyzing with Gemini...")
            analysis = analyze_with_gemini(paper.title, paper.summary)

            # Rate limit for Gemini (15 calls/min, 250k tokens/min, 1000 calls/day)
            # Wait 4.5 seconds between calls = ~13 calls/min (safely under limit)
            if analysis:  # Only sleep if we actually made a Gemini call
                time.sleep(4.5)

            if not analysis:
                # Use defaults if Gemini fails
                analysis = {
                    'score': 5,
                    'tldr': paper.title[:150],
                    'tags': ['Other']
                }

            # Extract authors
            authors = [author.name for author in paper.authors]

            # Prepare paper data
            paper_data = {
                'arxiv_id': arxiv_id,
                'title': paper.title,
                'abstract': paper.summary,
                'authors': authors,
                'published_at': paper.published.isoformat(),
                'url': paper.entry_id,
                'impact_score': analysis['score'],
                'summary': analysis['tldr'],
                'tags': analysis['tags'],
                'embedding': embedding,
                'posted_to_discord': False
            }

            # Save to database
            if save_paper(paper_data):
                print(f"   ✓ Saved (Score: {analysis['score']}/10)")
                stats['new'] += 1
            else:
                print(f"   ❌ Failed to save")

        except Exception as e:
            print(f"   ❌ Error processing paper: {e}")
            stats['errors'] += 1
            continue


def print_summary():
    """
    Print job summary statistics
    """
    print("\n" + "=" * 60)
    print("📊 JOB SUMMARY")
    print("=" * 60)
    print(f"Papers fetched:       {stats['fetched']}")
    print(f"New papers saved:     {stats['new']}")
    print(f"Duplicates skipped:   {stats['duplicates']}")
    print(f"Errors:               {stats['errors']}")
    print(f"Gemini API calls:     {stats['gemini_calls']}")
    print(f"Embedding API calls:  {stats['embedding_calls']}")
    print("=" * 60)


def main():
    """
    Main execution flow
    """
    print("=" * 60)
    print("🚀 ArXiv Paper Fetcher - Starting Daily Job")
    print("=" * 60)

    try:
        # Fetch papers
        papers = fetch_arxiv_papers()

        if not papers:
            print("⚠️  No papers found for yesterday")
            return

        # Process papers
        process_papers(papers)

        # Print summary
        print_summary()

        print("\n✅ Job completed successfully!")

    except Exception as e:
        print(f"\n❌ Job failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
