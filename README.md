# Explorative Scraping Pipeline

Open-source Azure Functions pipeline for discovering, extracting, reviewing, and storing structured records from public web sources.

The project is a configurable version of an explorative scraping backend: bring your own domain schema, source URLs, prompts, and Azure resources.

## What It Does

- Discovers candidate links from source pages.
- Extracts readable text from public URLs.
- Uses deterministic extraction by default and optional Azure OpenAI structured extraction.
- Reviews records against a configurable schema.
- Stores candidates, review items, approved records, source pages, run logs, and token usage in Azure Cosmos DB.
- Exposes HTTP endpoints for manual extraction, source screening, and searching stored records.
- Deploys to Azure Functions with azd and Bicep.

## Azure Components

Default deployment provisions:

- Azure Functions on Linux Flex Consumption.
- Azure Storage.
- Azure Cosmos DB for NoSQL.
- Application Insights and Log Analytics.
- Optional Azure OpenAI configuration via app settings.

## Quick Start

```powershell
python -m venv .venv
./.venv/Scripts/python.exe -m pip install -r requirements.txt -r requirements-dev.txt
./.venv/Scripts/python.exe -m pytest
```

Run locally with Azure Functions Core Tools:

```powershell
func start
```

## Deploy To Azure

[![Deploy to Azure](https://aka.ms/deploytoazurebutton)](https://portal.azure.com/#create/Microsoft.Template/uri/https%3A%2F%2Fraw.githubusercontent.com%2Fflo7up%2Fexplorative-scraping-pipeline%2Fmain%2Finfra%2Fmain.json)

The button deploys the generated ARM template in `infra/main.json`. Use `azd up` when you want the full code deployment flow.

### Recommended: Azure Developer CLI

```powershell
azd auth login
azd up
```

### GitHub Actions

The repo includes `.github/workflows/deploy.yml`. Configure these repository variables or secrets:

- `AZURE_CLIENT_ID`
- `AZURE_TENANT_ID`
- `AZURE_SUBSCRIPTION_ID`
- `AZURE_ENV_NAME`
- `AZURE_LOCATION`

The workflow uses OIDC and does not require publish profiles.

## Configuration

Copy `.env.example` to `local.settings.json` for local Functions development, or set matching app settings in Azure.

The pipeline behavior is controlled by `pipeline.config.json`:

- record type and domain description
- seed URLs and allowed domains
- output schema fields
- LLM deployment settings
- quality gates and duplicate behavior

## Cost Controls

The default configuration is conservative:

- no model call is required for deterministic extraction
- source text is truncated before model use
- source pages have revisit intervals
- candidate processing is queue based
- model calls are logged by function and deployment
- review-before-store can be enabled or disabled

## One-Click Deploy Button

After pushing this repository to GitHub, update the `repositoryUrl` parameter in `infra/main.parameters.json` and use the Azure Developer CLI button pattern in your README or GitHub release. The Bicep and azd files are already prepared for one-command deployment.

## Security

Do not commit secrets. Use Azure app settings, Key Vault, or GitHub Actions secrets. See `SECURITY.md`.

## License

MIT. See `LICENSE`.
