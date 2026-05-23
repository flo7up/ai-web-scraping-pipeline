# Microsoft Foundry / Azure AI Setup

The Azure deployment provisions an Azure AI Services resource that can be used from Microsoft Foundry and Azure OpenAI-compatible APIs.

## What The Template Provisions

- Azure AI Services account (`Microsoft.CognitiveServices/accounts`, kind `AIServices`)
- Function App setting `AZURE_OPENAI_ENDPOINT`
- Function App setting `AZURE_OPENAI_DEPLOYMENT`, initially empty unless provided as a parameter

## Model Deployment

The template does not deploy a model by default. This keeps provisioning predictable and avoids forcing a model choice or quota usage.

After deployment:

1. Open the Azure AI Services resource in Microsoft Foundry.
2. Create or select a project if prompted.
3. Deploy a chat model appropriate for extraction.
4. Copy the deployment name.
5. Set the Function App app setting `AZURE_OPENAI_DEPLOYMENT` to that deployment name.
6. Restart the Function App.

## Cost-Efficient Defaults

- If `AZURE_OPENAI_DEPLOYMENT` is empty, extraction falls back to deterministic extraction.
- Keep `llm.maxInputChars` in `pipeline.config.json` conservative.
- Start with a small seed list and low `maxLinksPerSource`.
- Monitor Application Insights and Azure AI token usage before increasing cadence.

## Authentication

The runtime supports Azure OpenAI key auth through `AZURE_OPENAI_API_KEY`, or Microsoft Entra authentication via `DefaultAzureCredential` when no key is supplied.

For production, prefer managed identity and role-based access where available.
