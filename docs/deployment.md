# Deployment

## Prerequisites

- Azure Developer CLI
- Azure CLI
- Azure Functions Core Tools
- Python 3.11

## Deploy

### Option A: One-click Azure resource deployment

Use the Deploy to Azure button in the README to provision:

- Azure Functions Flex Consumption plan and Function App
- Azure Storage
- Azure Cosmos DB account, database, and containers
- Azure AI Services resource for Microsoft Foundry / Azure OpenAI-compatible deployments
- Application Insights and Log Analytics

This path provisions resources. Use GitHub Actions or `azd up` when you also want to publish Function App code.

### Option B: Full deployment with Azure Developer CLI

```powershell
azd auth login
azd up
```

This provisions resources and deploys the Python Functions code.

## Configure GitHub OIDC

The included deploy workflow expects repository variables or secrets:

- `AZURE_CLIENT_ID`
- `AZURE_TENANT_ID`
- `AZURE_SUBSCRIPTION_ID`
- `AZURE_ENV_NAME`
- `AZURE_LOCATION`

Grant the federated identity permissions to deploy the resources in your target subscription or resource group.

## Microsoft Foundry model setup

The template creates an Azure AI Services resource, but it does not force a model deployment. This keeps one-click deployment broadly usable across subscriptions and quotas.

After deployment:

1. Open the Azure AI Services resource in Microsoft Foundry.
2. Deploy a chat model.
3. Set the Function App setting `AZURE_OPENAI_DEPLOYMENT` to the model deployment name.
4. Restart the Function App.

Without `AZURE_OPENAI_DEPLOYMENT`, deterministic extraction still works.

## Local Development

Copy `local.settings.sample.json` to `local.settings.json`, fill values, then run:

```powershell
func start
```
