# Prompt Customization

Prompt templates live under `prompts/` and are referenced from `pipeline.config.json`.

Default templates:

- `prompts/extraction.system.md`
- `prompts/extraction.user.md`
- `prompts/discovery.system.md`
- `prompts/discovery.user.md`
- `prompts/groundedness.system.md`
- `prompts/groundedness.user.md`

Configure different files with:

```json
{
	"prompts": {
		"discoverySystem": "prompts/discovery.system.md",
		"discoveryUser": "prompts/discovery.user.md",
		"extractionSystem": "prompts/extraction.system.md",
		"extractionUser": "prompts/extraction.user.md",
		"groundednessSystem": "prompts/groundedness.system.md",
		"groundednessUser": "prompts/groundedness.user.md"
	}
}
```

Discovery templates can use:

- `domainDescription`
- `recordType`
- `schemaJson`
- `allowedDomains`
- `seedUrls`
- `maxQueryCount`

Extraction templates can use:

- `domainDescription`
- `recordType`
- `schemaJson`
- `sourceUrl`
- `sourceTitle`
- `sourceText`

Groundedness templates can use:

- `groundednessThreshold`
- `sourceText`
- `recordClaims`

Keep prompts source-grounded. Do not ask the model to infer facts that are not present in source text.
