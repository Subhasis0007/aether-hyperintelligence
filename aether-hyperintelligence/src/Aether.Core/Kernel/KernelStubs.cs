namespace Aether.Core.Kernel;

public sealed class AetherConfig
{
    public DataClass DataClassification { get; set; } = DataClass.Public;
    public string OllamaEndpoint { get; set; } = "http://localhost:11434";
    public string AzureDeployment { get; set; } = "gpt-4o";
    public string AzureEndpoint { get; set; } = "https://example.openai.azure.com/";
    public string AzureKey { get; set; } = "replace-me";
}

public enum DataClass
{
    Public = 0,
    Internal = 1,
    Sensitive = 2,
    TopSecret = 3
}

public interface IPostQuantumProvider { }
public interface IAuditChain { }

public sealed class SapPlugin { public bool IsConfigured() => false; }
public sealed class SalesforcePlugin { public bool IsConfigured() => false; }
public sealed class ServiceNowPlugin { public bool IsConfigured() => false; }
public sealed class DynamicsPlugin { public bool IsConfigured() => false; }
public sealed class WorkdayPlugin { public bool IsConfigured() => false; }
public sealed class HubSpotPlugin { public bool IsConfigured() => false; }
public sealed class StripePlugin { public bool IsConfigured() => false; }
public sealed class MindSpherePlugin { public bool IsConfigured() => false; }
public sealed class OpcUaPlugin { public bool IsConfigured() => false; }
public sealed class NatsIoTPlugin { public bool IsConfigured() => false; }
public sealed class HyperledgerPlugin { public bool IsConfigured() => false; }
public sealed class SlackPlugin { public bool IsConfigured() => false; }
public sealed class TeamsPlugin { public bool IsConfigured() => false; }
public sealed class GitHubPlugin { public bool IsConfigured() => false; }
public sealed class SnowflakePlugin { public bool IsConfigured() => false; }

public sealed class Neo4jKnowledgeGraphPlugin { public bool IsConfigured() => false; }
public sealed class WeaviateRagPlugin { public bool IsConfigured() => false; }
public sealed class QdrantCachePlugin { public bool IsConfigured() => false; }
public sealed class ClickHouseAnalyticsPlugin { public bool IsConfigured() => false; }
public sealed class TemporalWorkflowPlugin { public bool IsConfigured() => false; }
public sealed class KafkaEventPlugin { public bool IsConfigured() => false; }
public sealed class PostQuantumPlugin { public bool IsConfigured() => false; }
public sealed class EbpfTracePlugin { public bool IsConfigured() => false; }
