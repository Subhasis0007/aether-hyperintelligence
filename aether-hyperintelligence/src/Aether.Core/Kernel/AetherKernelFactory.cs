using System;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;

namespace Aether.Core.Kernel;

public static class AetherKernelFactory
{
    public static Microsoft.SemanticKernel.Kernel CreateForTenant(
        string tenantId,
        AetherConfig config,
        IServiceProvider services,
        ILogger log)
    {
        var builder = Microsoft.SemanticKernel.Kernel.CreateBuilder();

        // Model routing: classify data sensitivity, route to correct LLM endpoint
        switch (config.DataClassification)
        {
            case DataClass.TopSecret:
            case DataClass.Sensitive:
                // On-premises only — Llama-3.1-70B via Ollama, zero cloud egress
                builder.AddOllamaChatCompletion(
                    modelId: "llama3.1:70b",
                    endpoint: new Uri(config.OllamaEndpoint));
                log.LogInformation("Tenant {Id}: routing to on-prem Ollama", tenantId);
                break;

            default:
                // Azure OpenAI gpt-4o with full function-calling capability
                builder.AddAzureOpenAIChatCompletion(
                    deploymentName: config.AzureDeployment,
                    endpoint: config.AzureEndpoint,
                    apiKey: config.AzureKey);
                break;
        }

        // Register all 25+ connector plugins
        builder.Plugins.AddFromType<SapPlugin>("SAP");
        builder.Plugins.AddFromType<SalesforcePlugin>("Salesforce");
        builder.Plugins.AddFromType<ServiceNowPlugin>("ServiceNow");
        builder.Plugins.AddFromType<DynamicsPlugin>("Dynamics");
        builder.Plugins.AddFromType<WorkdayPlugin>("Workday");
        builder.Plugins.AddFromType<HubSpotPlugin>("HubSpot");
        builder.Plugins.AddFromType<StripePlugin>("Stripe");
        builder.Plugins.AddFromType<MindSpherePlugin>("MindSphere");
        builder.Plugins.AddFromType<OpcUaPlugin>("OPCUA");
        builder.Plugins.AddFromType<NatsIoTPlugin>("IoT");
        builder.Plugins.AddFromType<HyperledgerPlugin>("Blockchain");
        builder.Plugins.AddFromType<SlackPlugin>("Slack");
        builder.Plugins.AddFromType<TeamsPlugin>("Teams");
        builder.Plugins.AddFromType<GitHubPlugin>("GitHub");
        builder.Plugins.AddFromType<SnowflakePlugin>("Snowflake");

        // Intelligence layer plugins
        builder.Plugins.AddFromType<Neo4jKnowledgeGraphPlugin>("KG");
        builder.Plugins.AddFromType<WeaviateRagPlugin>("RAG");
        builder.Plugins.AddFromType<QdrantCachePlugin>("Cache");
        builder.Plugins.AddFromType<ClickHouseAnalyticsPlugin>("Analytics");
        builder.Plugins.AddFromType<TemporalWorkflowPlugin>("Workflow");
        builder.Plugins.AddFromType<KafkaEventPlugin>("Events");
        builder.Plugins.AddFromType<PostQuantumPlugin>("Crypto");
        builder.Plugins.AddFromType<EbpfTracePlugin>("eBPF");

        builder.Services.AddSingleton(config);
        builder.Services.AddSingleton(services.GetRequiredService<IPostQuantumProvider>());
        builder.Services.AddSingleton(services.GetRequiredService<IAuditChain>());

        return builder.Build();
    }
}
