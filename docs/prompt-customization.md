# Prompt Customization

Prompt templates can be introduced under `src/pipeline/prompts/` as the pipeline evolves.

For v1, the extraction prompt is assembled from:

- `domainDescription`
- `recordType`
- `schema.fields`
- source URL/title/text

Keep prompts source-grounded. Do not ask the model to infer facts that are not present in source text.
