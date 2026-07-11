# ADR-005: Dual-Mode Semantic Search with sentence-transformers Default

**Status:** Accepted  
**Date:** 2026-05-04  
**Deciders:** Karthik Vaidhyanathan

---

## Context

Two capability areas require semantic (embedding-based) search:
- **Tool Registry** (REQ-TOOL-03): find the right tool by intent, not just keyword.
- **Agent Registry** (REQ-AREG-05): find the right agent by capability description.

The existing keyword search (substring match) is fast but fails for paraphrases and synonyms. Semantic search uses vector embeddings to match by meaning.

Three approaches exist for providing embeddings:

| Approach | Latency | Cost | Privacy | Install Size |
|---|---|---|---|---|
| `sentence-transformers` (local) | ~50–200 ms first call, ~5 ms cached | Free | Data stays local | ~1 GB (model + torch) |
| OpenAI `text-embedding-*` | ~100–500 ms (network) | Per-token API cost | Data leaves machine | ~10 KB (SDK only) |
| Custom / BYO | Varies | Varies | Varies | Varies |

---

## Decision

**Provide a pluggable `EmbeddingProvider` abstract interface. Ship `SentenceTransformerEmbeddingProvider` as the default implementation. Users who do not install `sentence-transformers` fall back gracefully to keyword-only search with a warning.**

### Interface

```python
class EmbeddingProvider(ABC):
    @abstractmethod
    def embed(self, texts: List[str]) -> List[List[float]]:
        """Return a list of embedding vectors, one per input text."""
```

### Default Provider

```python
class SentenceTransformerEmbeddingProvider(EmbeddingProvider):
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        # Lazy import — raises ImportError with a helpful message if not installed
        from sentence_transformers import SentenceTransformer
        self._model = SentenceTransformer(model_name)

    def embed(self, texts):
        return self._model.encode(texts, convert_to_numpy=True).tolist()
```

`all-MiniLM-L6-v2` is chosen as the default model: 80 MB on disk, 384-dimensional vectors, excellent speed/quality trade-off for short text (tool names, agent descriptions).

### Graceful Degradation

```python
def _get_default_embedding_provider() -> Optional[EmbeddingProvider]:
    try:
        return SentenceTransformerEmbeddingProvider()
    except ImportError:
        warnings.warn(
            "sentence-transformers not installed; semantic search disabled. "
            "Install with: pip install moya[semantic]",
            RuntimeWarning
        )
        return None
```

When `embedding_provider` is `None`, `find_by_semantic_similarity()` raises `SemanticSearchUnavailableError` with a clear install instruction.

### Vector Storage

Embedding vectors are stored alongside registry entries in the JSON/SQLite backend. Similarity search uses cosine similarity over the stored vectors (no external vector DB required for reasonable registry sizes — typically < 1000 entries).

---

## Alternatives Considered

**Require users to provide an embedding provider (no default):** Zero surprise about install size but adds friction for new users and makes the feature feel incomplete. Rejected.

**OpenAI embeddings as default:** Better quality but requires an API key and charges money. Not appropriate as a default for a local framework. Can be provided as an `OpenAIEmbeddingProvider` in `moya-skills` or similar.

**Integrate a vector DB (Chroma, Qdrant):** Overkill for < 1000 agents/tools. Adds a heavy dependency. Noted as a future extension point via the `EmbeddingProvider` + `VectorStore` interfaces.

---

## Consequences

- `sentence-transformers` and `torch` are optional: `pip install moya[semantic]`.
- First-time use triggers a model download (~80 MB). This is standard for the library and documented.
- The `EmbeddingProvider` interface means users can swap in any embedding service without changing registry code.
- Cosine similarity search is O(n) over the registry — acceptable for small-to-medium catalogs. If registries grow large, users can swap the backend for an ANN-capable vector store.
