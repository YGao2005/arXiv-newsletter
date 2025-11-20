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


def analyze_papers_batch(papers_batch: List[tuple]) -> Dict[str, Optional[Dict]]:
    """
    Analyze multiple papers in a single Gemini API call for efficiency
    papers_batch: List of (arxiv_id, title, abstract) tuples
    Returns: Dict mapping arxiv_id to analysis dict
    """
    if not papers_batch:
        return {}

    # Build batch prompt
    prompt = """You are a HIGHLY CRITICAL reviewer evaluating computer science research papers. Be strict and discriminating in your scoring.

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

Analyze each paper below and return a JSON array with one object per paper:

"""

    # Add each paper to the prompt
    for i, (arxiv_id, title, abstract) in enumerate(papers_batch):
        prompt += f"""
Paper {i+1} (ID: {arxiv_id}):
Title: {title}
Abstract: {abstract[:800]}{"..." if len(abstract) > 800 else ""}

"""

    prompt += """
Return ONLY a valid JSON array in this exact format:
[
  {"paper_id": "<arxiv_id>", "score": <number>, "tldr": "<string>", "tags": ["<tag1>", "<tag2>", ...]},
  ...
]

For each paper provide:
- "paper_id": The exact arxiv_id shown above
- "score": Integer 1-10 (BE CRITICAL - most should be 4-6)
- "tldr": Single concise sentence (max 150 chars) summarizing key contribution
- "tags": Array of 2-5 tags from: ["CV", "NLP", "LLM", "Transformers", "Diffusion", "RL", "Robotics", "ML", "Theory", "Systems", "Security", "Other"]
"""

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

        # Parse JSON array
        analyses = json.loads(text)

        if not isinstance(analyses, list):
            raise ValueError("Expected JSON array from Gemini")

        # Convert to dict mapping arxiv_id to analysis
        results = {}
        for analysis in analyses:
            if 'paper_id' in analysis and all(k in analysis for k in ['score', 'tldr', 'tags']):
                paper_id = analysis['paper_id']
                results[paper_id] = {
                    'score': max(1, min(10, int(analysis['score']))),
                    'tldr': analysis['tldr'],
                    'tags': analysis['tags']
                }

        return results

    except Exception as e:
        print(f"⚠️  Error analyzing batch with Gemini: {e}")
        print(f"   Response: {response.text if 'response' in locals() else 'N/A'}")
        # Return empty dict - caller will handle defaults
        return {}


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
    Process papers in batches: generate embeddings, analyze with Gemini in batches
    """
    BATCH_SIZE = 10  # Process 10 papers per Gemini call
    print(f"\n🔄 Processing {len(papers)} papers in batches of {BATCH_SIZE}...")

    # Filter out papers that already exist
    papers_to_process = []
    for paper in papers:
        arxiv_id = paper.entry_id.split('/abs/')[-1]
        if check_paper_exists(arxiv_id):
            stats['duplicates'] += 1
        else:
            papers_to_process.append(paper)

    print(f"   📝 {len(papers_to_process)} new papers to process ({stats['duplicates']} duplicates skipped)")

    # Process in batches
    for batch_start in range(0, len(papers_to_process), BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, len(papers_to_process))
        batch_papers = papers_to_process[batch_start:batch_end]
        batch_num = (batch_start // BATCH_SIZE) + 1
        total_batches = (len(papers_to_process) + BATCH_SIZE - 1) // BATCH_SIZE

        print(f"\n📦 Batch {batch_num}/{total_batches} ({len(batch_papers)} papers)")

        # Step 1: Generate embeddings for all papers in batch
        print(f"   🧠 Generating embeddings...")
        papers_with_embeddings = []
        for paper in batch_papers:
            arxiv_id = paper.entry_id.split('/abs/')[-1]
            embed_text = f"{paper.title}. {paper.summary}"
            embedding = get_embedding(embed_text)

            if embedding:
                papers_with_embeddings.append((paper, arxiv_id, embedding))
            else:
                print(f"      ⚠️  Failed embedding for {arxiv_id}, skipping")
                stats['errors'] += 1

        if not papers_with_embeddings:
            print(f"   ⚠️  No valid embeddings in this batch, skipping")
            continue

        # Step 2: Analyze all papers in batch with single Gemini call
        print(f"   ✨ Analyzing {len(papers_with_embeddings)} papers with Gemini...")
        batch_for_gemini = [(arxiv_id, paper.title, paper.summary) for paper, arxiv_id, _ in papers_with_embeddings]
        analyses = analyze_papers_batch(batch_for_gemini)

        # Rate limit: 4.5 seconds between batch calls
        time.sleep(4.5)

        # Step 3: Save papers to database
        print(f"   💾 Saving to database...")
        for paper, arxiv_id, embedding in papers_with_embeddings:
            try:
                # Get analysis or use defaults
                analysis = analyses.get(arxiv_id, {
                    'score': 5,
                    'tldr': paper.title[:150],
                    'tags': ['Other']
                })

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
                    stats['new'] += 1
                else:
                    stats['errors'] += 1

            except Exception as e:
                print(f"      ❌ Error saving {arxiv_id}: {e}")
                stats['errors'] += 1

        print(f"   ✓ Batch complete - saved {len(papers_with_embeddings)} papers")
        score_summary = {}
        for arxiv_id in analyses:
            score = analyses[arxiv_id]['score']
            score_summary[score] = score_summary.get(score, 0) + 1
        if score_summary:
            print(f"      Score distribution: {dict(sorted(score_summary.items()))}")


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
