"""
HuggingFace Space - Embedding API
Lightweight stateless API for generating text embeddings
"""

import os
from flask import Flask, request, jsonify
from sentence_transformers import SentenceTransformer
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Load the embedding model (all-MiniLM-L6-v2, 384 dimensions)
# This model is small (~80MB) and fast on CPU
logger.info("Loading embedding model...")
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
logger.info("Model loaded successfully!")


@app.route('/')
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "model": "all-MiniLM-L6-v2",
        "dimensions": 384,
        "endpoints": {
            "/embed": "POST - Generate embeddings for text",
            "/batch_embed": "POST - Generate embeddings for multiple texts"
        }
    })


@app.route('/embed', methods=['POST'])
def embed_text():
    """
    Generate embedding for a single text query

    Request body:
    {
        "text": "Your text here"
    }

    Response:
    {
        "embedding": [0.123, -0.456, ...],
        "dimensions": 384
    }
    """
    try:
        data = request.get_json()

        if not data or 'text' not in data:
            return jsonify({
                "error": "Missing 'text' field in request body"
            }), 400

        text = data['text']

        if not isinstance(text, str) or len(text.strip()) == 0:
            return jsonify({
                "error": "Text must be a non-empty string"
            }), 400

        # Generate embedding
        embedding = model.encode(text, convert_to_numpy=True)

        return jsonify({
            "embedding": embedding.tolist(),
            "dimensions": len(embedding)
        })

    except Exception as e:
        logger.error(f"Error generating embedding: {str(e)}")
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500


@app.route('/batch_embed', methods=['POST'])
def batch_embed_texts():
    """
    Generate embeddings for multiple texts (batch processing)

    Request body:
    {
        "texts": ["Text 1", "Text 2", ...]
    }

    Response:
    {
        "embeddings": [[0.123, ...], [0.456, ...], ...],
        "count": 2,
        "dimensions": 384
    }
    """
    try:
        data = request.get_json()

        if not data or 'texts' not in data:
            return jsonify({
                "error": "Missing 'texts' field in request body"
            }), 400

        texts = data['texts']

        if not isinstance(texts, list) or len(texts) == 0:
            return jsonify({
                "error": "Texts must be a non-empty list"
            }), 400

        # Limit batch size to prevent abuse
        if len(texts) > 100:
            return jsonify({
                "error": "Batch size too large (max 100 texts)"
            }), 400

        # Generate embeddings
        embeddings = model.encode(texts, convert_to_numpy=True)

        return jsonify({
            "embeddings": embeddings.tolist(),
            "count": len(embeddings),
            "dimensions": embeddings.shape[1] if len(embeddings) > 0 else 384
        })

    except Exception as e:
        logger.error(f"Error generating batch embeddings: {str(e)}")
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500


if __name__ == '__main__':
    # HuggingFace Spaces requires the app to listen on port 7860
    port = int(os.environ.get('PORT', 7860))
    logger.info(f"Starting server on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=False)
