# Microsoft Foundry / Azure AI Setup

The Azure deployment provisions an Azure AI Services resource that can be used from Microsoft Foundry and Azure OpenAI-compatible APIs.

## What The Template Provisions

- Azure AI Services account (`Microsoft.CognitiveServices/accounts`, kind `AIServices`)
- Function App setting `AZURE_OPENAI_ENDPOINT`
- Function App setting `AZURE_OPENAI_DEPLOYMENT`, initially empty unless provided as a parameter

## Model Deployment

The template creates the Azure AI Services resource but does not create model deployments. Configure model deployments before operational pipeline runs; empty deployment settings are suitable only while provisioning infrastructure.

After deployment:

1. Open the Azure AI Services resource in Microsoft Foundry.
2. Create or select a project if prompted.
3. Deploy a chat model appropriate for structured extraction.
4. Deploy an embedding model for provider-neutral duplicate detection.
5. Deploy a groundedness model for LLM groundedness checks.
6. Set the Function App app settings `AZURE_OPENAI_DEPLOYMENT`, `AZURE_OPENAI_EMBEDDING_DEPLOYMENT`, and `AZURE_OPENAI_GROUNDEDNESS_DEPLOYMENT` to those deployment names.
7. Restart the Function App.

## Cost-Efficient Defaults

- Keep `llm.maxInputChars` in `pipeline.config.json` conservative.
- Start with a small seed list and low `maxLinksPerSource`.
- Monitor Application Insights and Azure AI token usage before increasing cadence.

## Authentication

The runtime supports Azure OpenAI key auth through `AZURE_OPENAI_API_KEY`, or Microsoft Entra authentication via `DefaultAzureCredential` when no key is supplied.

For production, prefer managed identity and role-based access where available.
