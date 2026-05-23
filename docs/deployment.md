# Deployment

## Prerequisites

- Azure Developer CLI
- Azure CLI
- Azure Functions Core Tools
- Python 3.11

## Deploy

```powershell
azd auth login
azd up
```

## Configure GitHub OIDC

The included deploy workflow expects repository variables or secrets:

- `AZURE_CLIENT_ID`
- `AZURE_TENANT_ID`
- `AZURE_SUBSCRIPTION_ID`
- `AZURE_ENV_NAME`
- `AZURE_LOCATION`

Grant the federated identity permissions to deploy the resources in your target subscription or resource group.

## Local Development

Copy `local.settings.sample.json` to `local.settings.json`, fill values, then run:

```powershell
func start
```
