---
title: ArXiv Embedding API
emoji: 📚
colorFrom: blue
colorTo: purple
sdk: docker
pinned: false
---

# ArXiv Papers Bot - Embedding API

This HuggingFace Space provides a lightweight embedding API for the ArXiv Papers Discord Bot.

## Endpoints

### `GET /`
Health check endpoint

### `POST /embed`
Generate embedding for a single text query

**Request:**
```json
{
  "text": "transformer architecture for computer vision"
}
```

**Response:**
```json
{
  "embedding": [0.123, -0.456, ...],
  "dimensions": 384
}
```

### `POST /batch_embed`
Generate embeddings for multiple texts (max 100)

**Request:**
```json
{
  "texts": ["Text 1", "Text 2", "Text 3"]
}
```

**Response:**
```json
{
  "embeddings": [[...], [...], [...]],
  "count": 3,
  "dimensions": 384
}
```

## Model

- **Model:** sentence-transformers/all-MiniLM-L6-v2
- **Dimensions:** 384
- **Size:** ~80MB
- **Speed:** Optimized for CPU inference

## Deployment to HuggingFace Spaces

1. Create a new Space on HuggingFace
2. Select "Docker" as the SDK
3. Upload all files from this directory
4. The Space will automatically build and deploy

No secrets required for this service!
