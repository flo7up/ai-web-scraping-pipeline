# Explorative Scraping Pipeline

Open-source Azure Functions pipeline for discovering, extracting, reviewing, and storing structured records from public web sources.

The project is a configurable version of an explorative scraping backend: bring your own domain schema, source URLs, prompts, and Azure resources.

## What It Does

- Discovers candidate links from source pages.
- Extracts readable text from public URLs.
- Uses deterministic extraction by default and optional Azure OpenAI structured extraction.
- Reviews records against a configurable schema.
- Checks for duplicates by exact source identity and, when embeddings are configured, provider-neutral vector similarity.
- Evaluates groundedness against the fetched source text and stores the score, result, reason, and threshold on approved records.
- Stores candidates, review items, approved records, source pages, run logs, and token usage in Azure Cosmos DB.
- Exposes HTTP endpoints for manual extraction, source screening, and searching stored records.
- Deploys to Azure Functions with azd and Bicep.

## Azure Components

Default deployment provisions:

- Azure Functions on Linux Flex Consumption.
- Azure Storage.
- Azure Cosmos DB for NoSQL.
- Cosmos DB vector search on the `Records` container for embedding-based duplicate detection.
- Azure AI Services resource for Microsoft Foundry / Azure OpenAI compatible deployments.
- Application Insights and Log Analytics.
- Function app settings wired to Cosmos DB and the Azure AI endpoint.

Model deployment is intentionally configurable: the template creates the Azure AI Services/Foundry-capable resource, then you choose deployment names and set `AZURE_OPENAI_DEPLOYMENT`, `AZURE_OPENAI_EMBEDDING_DEPLOYMENT`, and `AZURE_OPENAI_GROUNDEDNESS_DEPLOYMENT` as needed. Deterministic extraction and deterministic groundedness fallback work without model calls.

## Quick Start

### 1. Clone and install

```powershell
git clone https://github.com/flo7up/explorative-scraping-pipeline.git
cd explorative-scraping-pipeline
python -m venv .venv
./.venv/Scripts/python.exe -m pip install -r requirements.txt -r requirements-dev.txt
./.venv/Scripts/python.exe -m pytest
```

### 2. Configure the scraping domain

Edit `pipeline.config.json`:

- `domainDescription`: what kind of records you want to find
- `sourceDiscovery.seedUrls`: starting pages to explore
- `sourceDiscovery.allowedDomains`: optional domain allow-list
- `schema.fields`: the structured output fields

See `docs/use-cases.md` for examples, including an AIUseCaseHub-style use case pipeline.

### 3. Run locally

Run locally with Azure Functions Core Tools:

```powershell
Copy-Item local.settings.sample.json local.settings.json
func start
```

## Deploy To Azure

[![Deploy to Azure](https://aka.ms/deploytoazurebutton)](https://portal.azure.com/#create/Microsoft.Template/uri/https%3A%2F%2Fraw.githubusercontent.com%2Fflo7up%2Fexplorative-scraping-pipeline%2Fmain%2Finfra%2Fmain.json)

The button deploys the generated ARM template in `infra/main.json` and provisions Azure Functions, Cosmos DB, Azure AI Services, Storage, and Application Insights. It also configures the `Records` container for Cosmos DB vector search. Use `azd up` when you want the full infrastructure + code deployment flow.

### Recommended: Azure Developer CLI

```powershell
azd auth login
azd up
```

After deployment, configure the model deployments you want to use:

1. Open the provisioned Azure AI Services resource in Microsoft Foundry.
2. Deploy a chat model and set `AZURE_OPENAI_DEPLOYMENT` for structured extraction.
3. Deploy an embedding model and set `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` for vector duplicate detection.
4. Optionally set `AZURE_OPENAI_GROUNDEDNESS_DEPLOYMENT` for LLM groundedness checks; otherwise the pipeline uses deterministic token-overlap groundedness.
5. Keep `llm.maxInputChars` and `groundedness.maxInputChars` conservative until you understand token usage.

### GitHub Actions

The repo includes `.github/workflows/deploy.yml`. Configure these repository variables or secrets:

- `AZURE_CLIENT_ID`
- `AZURE_TENANT_ID`
- `AZURE_SUBSCRIPTION_ID`
- `AZURE_ENV_NAME`
- `AZURE_LOCATION`

The workflow uses OIDC and does not require publish profiles.

## Example Use Cases

This repository can power different explorative scraping pipelines by changing config and prompts:

- AI use case discovery, like AIUseCaseHub.com.
- Customer case study discovery for a specific vendor ecosystem.
- Sustainability project discovery.
- Public sector digital-service examples.
- Competitor launch monitoring.
- Research-to-product signal tracking.

See `docs/use-cases.md` and `examples/`.

## Configuration

Copy `.env.example` to `local.settings.json` for local Functions development, or set matching app settings in Azure.

The pipeline behavior is controlled by `pipeline.config.json`:

- record type and domain description
- seed URLs and allowed domains
- output schema fields
- LLM deployment settings
- embedding and groundedness deployment settings
- quality gates, duplicate thresholds, and groundedness behavior

## Cost Controls

The default configuration is conservative:

- no model call is required for deterministic extraction
- no model call is required for deterministic groundedness fallback
- source text is truncated before model use
- source pages have revisit intervals
- candidate processing is queue based
- model calls are logged by function and deployment
- review-before-store can be enabled or disabled

## One-Click Deploy Button

The portal button is already wired for `flo7up/explorative-scraping-pipeline`. If you fork this repo, update the raw GitHub URL in the README button to point to your fork's `infra/main.json`.

## Security

Do not commit secrets. Use Azure app settings, Key Vault, or GitHub Actions secrets. See `SECURITY.md`.

## License

MIT. See `LICENSE`.
