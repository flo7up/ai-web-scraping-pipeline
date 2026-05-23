# Configuration

The primary configuration file is `pipeline.config.json`.

## Source Discovery

- `seedUrls`: starting pages for exploration.
- `allowedDomains`: optional domain allow-list.
- `blockedDomains`: domain block-list.
- `revisitFrequencyDays`: when source pages become due again.
- `maxLinksPerSource`: candidate cap per source page.

## Schema

Schema fields describe the target record. Required fields are enforced by the review stage.

## LLM Settings

- `deploymentNameEnv`: app setting that contains the Azure OpenAI deployment name.
- `maxInputChars`: source text truncation to control cost.
- `temperature`: keep low for structured extraction.

## Environment Settings

See `.env.example` and `local.settings.sample.json`.
