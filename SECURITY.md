# Security Policy

## Supported Versions

The `main` branch is the supported development version until the first tagged release.

## Reporting A Vulnerability

Please report security issues privately through GitHub Security Advisories if enabled for the repository, or by contacting the repository maintainers.

Do not open public issues for vulnerabilities that expose credentials, deployment details, or exploitable behavior.

## Secrets

Never commit:

- Azure OpenAI keys
- Cosmos DB connection strings
- Function keys
- Storage keys
- GitHub tokens
- Source credentials

Use Azure app settings, Key Vault, managed identity, or GitHub Actions secrets.
