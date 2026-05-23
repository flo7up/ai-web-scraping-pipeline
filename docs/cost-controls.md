# Cost Controls

The template defaults to conservative behavior.

- Deterministic extraction works without model calls.
- Azure OpenAI extraction only runs when endpoint and deployment settings are present.
- Embedding-based duplicate detection only calls the embedding model when `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` is set.
- Groundedness uses a deterministic fallback unless `AZURE_OPENAI_GROUNDEDNESS_DEPLOYMENT` is set.
- Source text is truncated by `llm.maxInputChars`.
- Groundedness source text is truncated by `groundedness.maxInputChars`.
- Source pages have revisit intervals.
- Candidate queues decouple discovery from extraction.
- Review gates prevent storing low-quality records.
- Application Insights should be used to monitor failures and dependencies.

Recommended first deployment:

1. Use a small seed URL list.
2. Keep `maxLinksPerSource` between 10 and 25.
3. Verify deterministic extraction first.
4. Enable Azure OpenAI extraction after the pipeline path is working.
5. Add embeddings and groundedness model deployments after reviewing expected review volume.
6. Review token, embedding, vector query, and function execution costs before increasing cadence.
