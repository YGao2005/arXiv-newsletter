# Sharing Supabase Database Across Multiple Bots

This guide explains how to use a single Supabase database for multiple Discord bots.

## Why Share a Database?

**Supabase Free Tier Limits:**
- Only **2 active projects** allowed
- 500MB database per project
- 2GB bandwidth per month

**Benefits of sharing:**
- ✅ Maximize free tier usage
- ✅ Centralized data management
- ✅ Easier backups and monitoring
- ✅ Shared extensions (like pgvector)

## Table Naming Strategy

We use **table prefixes** to organize bot data:

```
Shared Supabase Database:
├── ucla_classes              (UCLA Class Monitor bot)
├── ucla_subscriptions
├── internship_postings       (Internship Tracker bot)
├── arxiv_papers              (ArXiv Papers bot)
├── (future bot tables)
```

### Prefix Convention

| Bot | Prefix | Example Tables |
|-----|--------|----------------|
| UCLA Class Monitor | `ucla_` | `ucla_classes`, `ucla_subscriptions` |
| Internship Tracker | `internship_` | `internship_postings` |
| ArXiv Papers | `arxiv_` | `arxiv_papers` |
| Future bots | `{bot}_` | `{bot}_table_name` |

## How This Bot Is Configured

### 1. Tables Use Prefix

All tables created by this bot use the `arxiv_` prefix:
- `arxiv_papers` - Main papers table

### 2. Functions Use Prefix

All database functions use the `arxiv_` prefix:
- `arxiv_match_papers()` - Vector similarity search
- `arxiv_search_papers_fulltext()` - Text search
- `arxiv_get_unposted_papers()` - Get unposted papers

### 3. RLS Policies Use Prefix

Row-level security policies are named with prefixes:
- `arxiv_public_read_access`
- `arxiv_service_role_write_access`

### 4. Shared Resources

Some database features are shared across all bots:
- **Extensions**: `vector` (for pgvector)
- **Functions**: `update_updated_at_column()` (timestamp trigger)

These use `CREATE OR REPLACE` so multiple bots can safely create them.

## Environment Variables Setup

### For discord-bots-launcher

Update `.env` in the launcher to share Supabase:

```bash
# Shared Supabase (used by all bots)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_service_role_key

# Bot-specific tokens
DISCORD_TOKEN=ucla_bot_token
INTERNSHIP_BOT_TOKEN=internship_bot_token
ARXIV_BOT_TOKEN=arxiv_bot_token

# Bot-specific channels
CHANNEL_ID=arxiv_channel_id
INTERNSHIP_CHANNEL_ID=internship_channel_id
```

### For Standalone Deployment

If running the ArXiv bot standalone:

```bash
ARXIV_BOT_TOKEN=your_token
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key  # For read operations
CHANNEL_ID=your_channel_id
```

### For GitHub Actions

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your_service_role_key  # For write operations
GEMINI_API_KEY=your_gemini_key
HF_EMBED_API_URL=https://your-space.hf.space
```

## Migration Strategy

### 1. Apply to Existing Database

If you already have a Supabase database with other bots:

```bash
# 1. Open Supabase dashboard
# 2. Go to SQL Editor
# 3. Copy contents of supabase/migrations/001_initial_schema.sql
# 4. Paste and run
```

The migration is safe to run on an existing database because:
- Tables use `arxiv_` prefix (no conflicts)
- `create extension if not exists` won't fail if already exists
- Functions use `create or replace` (safe to re-run)

### 2. Verify No Conflicts

After running the migration, check for conflicts:

```sql
-- List all tables
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;

-- Should see:
-- arxiv_papers (new)
-- internship_postings (existing)
-- ucla_classes (existing)
-- etc.
```

## Database Size Monitoring

Keep track of database size to avoid hitting the 500MB limit:

```sql
-- Check total database size
SELECT pg_size_pretty(pg_database_size(current_database())) as size;

-- Check size per table
SELECT
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### Estimated Sizes

| Bot | Est. Size | Notes |
|-----|-----------|-------|
| UCLA Classes | ~10MB | Class listings + subscriptions |
| Internships | ~5MB | Job postings |
| ArXiv Papers | ~50MB | 1000 papers with embeddings (~50KB each) |
| **Total** | **~65MB** | Well under 500MB limit |

## Best Practices

### 1. Use Appropriate API Keys

**Anon Key** (read-only):
- Use in Discord bots for reading data
- Limited permissions via RLS policies
- Safe to use in client-side code

**Service Role Key** (full access):
- Use in GitHub Actions for writing data
- Has superuser permissions
- ⚠️ **Never commit to git or expose publicly**

### 2. Test Migrations Locally

Before applying to production:

```bash
# Use Supabase CLI to test locally
supabase db reset
supabase db push
```

### 3. Keep Migrations Idempotent

Migrations should be safe to run multiple times:
- Use `CREATE TABLE IF NOT EXISTS`
- Use `CREATE OR REPLACE FUNCTION`
- Use `CREATE EXTENSION IF NOT EXISTS`

### 4. Document Schema Changes

When adding new tables/functions:
1. Update migration file
2. Update this documentation
3. Add to the table prefix list

## Troubleshooting

### Error: "relation already exists"

**Cause**: Table name conflicts (missing prefix)

**Solution**: Ensure all tables use `arxiv_` prefix

### Error: "policy already exists"

**Cause**: Policy names conflict with other bots

**Solution**: Rename policies with `arxiv_` prefix

### Error: "function already exists"

**Cause**: Function name conflicts

**Solution**: Either:
- Use `CREATE OR REPLACE FUNCTION` (for shared functions)
- Add `arxiv_` prefix (for bot-specific functions)

### Database Size Exceeded

**Cause**: Approaching 500MB limit

**Solutions**:
1. Delete old data:
```sql
-- Delete papers older than 6 months
DELETE FROM arxiv_papers
WHERE published_at < NOW() - INTERVAL '6 months';
```

2. Upgrade to Supabase Pro ($25/month for 8GB)

3. Use a second Supabase project for less-used bots

## Future Considerations

### When to Split Into Multiple Databases

Consider creating a second Supabase project if:
- Total size approaches 400MB (80% of limit)
- Bandwidth exceeds 1.5GB/month
- Different bots need different hosting regions
- Security isolation is required

### Alternative: Use Schemas

For better isolation, consider using separate PostgreSQL schemas:

```sql
CREATE SCHEMA arxiv;
CREATE TABLE arxiv.papers (...);
```

This provides better namespacing but requires more complex RLS policies.

## Summary

**Current Setup:**
- ✅ Single Supabase database
- ✅ Table prefixes for organization
- ✅ Shared extensions (pgvector)
- ✅ Isolated RLS policies
- ✅ ~65MB total size (13% of free tier)

**Cost:** $0/month (within free tier)

This architecture supports 3-5 bots comfortably within Supabase's free tier limits.
