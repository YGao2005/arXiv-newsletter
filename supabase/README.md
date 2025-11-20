# Supabase Database Setup

This directory contains the database migrations for the ArXiv Papers Bot.

## 🔄 Shared Database Support

**This bot is designed to share a Supabase database with other bots!**

All tables and functions use the `arxiv_` prefix to avoid conflicts. You can safely run this migration on a Supabase database that already has other bot tables.

See [SHARED_DATABASE.md](../SHARED_DATABASE.md) for details.

## Prerequisites

- A Supabase account (free tier is sufficient)
- A Supabase project (can be shared with other bots)

## Setup Instructions

### 1. Create a Supabase Project

1. Go to [Supabase](https://supabase.com)
2. Create a new project
3. Wait for the project to initialize (~2 minutes)

### 2. Apply Database Migrations

#### Option A: Using Supabase Dashboard (Recommended for beginners)

1. Navigate to your Supabase project dashboard
2. Click on **SQL Editor** in the left sidebar
3. Open the file `migrations/001_initial_schema.sql`
4. Copy the entire contents
5. Paste into the SQL Editor
6. Click **Run** (or press Cmd/Ctrl + Enter)
7. Verify success - you should see "Success. No rows returned"

#### Option B: Using Supabase CLI (Recommended for advanced users)

```bash
# Install Supabase CLI
npm install -g supabase

# Login to Supabase
supabase login

# Link your project
supabase link --project-ref your-project-ref

# Apply migrations
supabase db push
```

### 3. Get Your API Keys

After applying migrations, get your API keys:

1. Go to **Project Settings** → **API**
2. Copy the following:
   - **Project URL** (looks like `https://xxxxx.supabase.co`)
   - **anon/public key** (for the Discord bot - read access)
   - **service_role key** (for GitHub Actions - write access)

⚠️ **IMPORTANT**: Keep your `service_role` key secure! It has full database access.

### 4. Verify Setup

Run this query in the SQL Editor to verify everything is set up correctly:

```sql
-- Check if vector extension is enabled
SELECT * FROM pg_extension WHERE extname = 'vector';

-- Check if tables exist
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public';

-- Check if functions exist
SELECT routine_name FROM information_schema.routines
WHERE routine_schema = 'public'
AND routine_type = 'FUNCTION';
```

You should see:
- The `vector` extension
- The `papers` table
- Functions: `match_papers`, `search_papers_fulltext`, `get_unposted_papers`

## Database Schema

### `arxiv_papers` Table

| Column | Type | Description |
|--------|------|-------------|
| `id` | bigint | Primary key |
| `arxiv_id` | text | Unique ArXiv identifier |
| `title` | text | Paper title |
| `abstract` | text | Paper abstract |
| `authors` | text[] | Array of author names |
| `published_at` | timestamp | Publication date |
| `url` | text | ArXiv URL |
| `impact_score` | int | AI-generated score (1-10) |
| `summary` | text | One-sentence TL;DR |
| `tags` | text[] | Category tags |
| `embedding` | vector(384) | Semantic embedding |
| `posted_to_discord` | boolean | Whether posted to Discord |
| `last_posted_at` | timestamp | When posted |
| `created_at` | timestamp | Record creation time |
| `updated_at` | timestamp | Last update time |

### Functions

#### `arxiv_match_papers(query_embedding, match_threshold, match_count)`
Performs vector similarity search.

**Parameters:**
- `query_embedding`: vector(384) - The query embedding
- `match_threshold`: float - Minimum similarity (0-1)
- `match_count`: int - Max results

**Returns:** Papers ranked by similarity

#### `arxiv_search_papers_fulltext(search_query, match_count)`
Performs full-text search as a fallback.

**Parameters:**
- `search_query`: text - Search keywords
- `match_count`: int - Max results

**Returns:** Papers matching the text query

#### `arxiv_get_unposted_papers(min_impact_score)`
Gets high-impact papers not yet posted to Discord.

**Parameters:**
- `min_impact_score`: int - Minimum score threshold

**Returns:** Unposted papers above the threshold

## Security Notes

- Row Level Security (RLS) is enabled
- Public read access is allowed (for the bot)
- Write access requires service role key
- The `anon` key should be used in the Discord bot
- The `service_role` key should only be used in GitHub Actions
- All policies are prefixed with `arxiv_` to avoid conflicts with other bots

## Troubleshooting

### Error: "extension vector does not exist"

Make sure you ran the migration that creates the extension:
```sql
create extension if not exists vector;
```

### Error: "function match_papers does not exist"

The function creation failed. Re-run the entire migration script.

### Performance Issues

If vector searches are slow:
1. Check that the HNSW index exists:
```sql
SELECT indexname FROM pg_indexes WHERE tablename = 'arxiv_papers';
```

2. If missing, create it:
```sql
CREATE INDEX arxiv_papers_embedding_idx ON arxiv_papers
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

### Sharing Database with Other Bots

If using the same database for multiple bots, see [SHARED_DATABASE.md](../SHARED_DATABASE.md) for:
- Table naming conventions
- API key management
- Database size monitoring
- Best practices
