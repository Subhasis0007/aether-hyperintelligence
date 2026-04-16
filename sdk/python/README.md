# AETHER Python SDK

Official async-first Python SDK for AETHER.

## Install

```bash
pip install .import asyncio
from aether_sdk import AetherClient

async def main():
    async with AetherClient(api_key="aeth_live_xxx", tenant="acme") as client:
        result = await client.intelligence.query(
            "Which of our top 20 customers are at churn risk this quarter?",
            systems=["Salesforce", "Stripe", "ServiceNow", "Dynamics"],
            explain=True,
        )
        print(result)

        incident = await client.teams.incident_command.invoke(
            incident_id="INC0123456",
            auto_deploy=True,
        )
        print(incident)

asyncio.run(main())This is the Python SDK scaffold for the AETHER platform.
The current client structure is async-first.
API methods can be wired to the real backend incrementally.