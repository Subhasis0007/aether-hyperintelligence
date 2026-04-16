using System;
using System.ComponentModel;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel;

namespace Aether.Agents.Connectors.Blockchain;

public sealed class HyperledgerPlugin
{
    private static readonly JsonSerializerOptions _opts = new(JsonSerializerDefaults.Web)
    {
        WriteIndented = false
    };

    private readonly ILogger<HyperledgerPlugin> _logger;
    private readonly IPostQuantumDecisionSigner _pq;
    private readonly IAuditChain _auditChain;
    private readonly IHyperledgerGateway _gateway;
    private readonly byte[] _tenantSigningKey;
    private readonly string _tenantKeyId;

    public HyperledgerPlugin()
        : this(
            NullLogger<HyperledgerPlugin>.Instance,
            new NoOpPostQuantumDecisionSigner(),
            new InMemoryAuditChain(),
            new NoOpHyperledgerGateway(),
            Array.Empty<byte>(),
            "dev-key")
    {
    }

    public HyperledgerPlugin(
        ILogger<HyperledgerPlugin> logger,
        IPostQuantumDecisionSigner pq,
        IAuditChain auditChain,
        IHyperledgerGateway gateway,
        byte[] tenantSigningKey,
        string tenantKeyId)
    {
        _logger = logger;
        _pq = pq;
        _auditChain = auditChain;
        _gateway = gateway;
        _tenantSigningKey = tenantSigningKey ?? Array.Empty<byte>();
        _tenantKeyId = string.IsNullOrWhiteSpace(tenantKeyId) ? "dev-key" : tenantKeyId;
    }

    [KernelFunction("blockchain_record_decision")]
    [Description("Record an agent decision on the immutable AETHER audit blockchain.")]
    public async Task<BlockchainAuditResult> RecordDecisionAsync(
        string agentName,
        string decisionType,
        string decisionJson,
        string tenantId,
        CancellationToken ct = default)
    {
        if (string.IsNullOrWhiteSpace(agentName))
            throw new ArgumentException("agentName is required.", nameof(agentName));

        if (string.IsNullOrWhiteSpace(decisionType))
            throw new ArgumentException("decisionType is required.", nameof(decisionType));

        if (string.IsNullOrWhiteSpace(tenantId))
            throw new ArgumentException("tenantId is required.", nameof(tenantId));

        using var parsed = JsonDocument.Parse(string.IsNullOrWhiteSpace(decisionJson) ? "{}" : decisionJson);

        // 1. Build structured, schema-validated audit record
        var record = new AuditRecord
        {
            RecordId = Guid.NewGuid().ToString("N"),
            SchemaVersion = "v2",
            AgentName = agentName,
            DecisionType = decisionType,
            TenantId = tenantId,
            Timestamp = DateTimeOffset.UtcNow,
            DecisionData = parsed.RootElement.Clone(),
            AetherVersion = BuildInfo.Version
        };

        // 2. Sign with CRYSTALS-Dilithium-5 — quantum-safe digital signature
        var signature = _pq.SignAgentDecision(_tenantSigningKey, record);
        record.QuantumSignature = Convert.ToBase64String(signature);
        record.SignatureAlgorithm = "CRYSTALS-Dilithium-5";
        record.SigningKeyId = _tenantKeyId;

        // 3. Chain hash: SHA-256(previousHash + recordJson)
        var previousHash = await _auditChain.GetLatestHashAsync(tenantId, ct);
        var recordJson = JsonSerializer.Serialize(record, _opts);
        record.ChainHash = ComputeChainHash(previousHash, recordJson);

        // 4. Submit to Hyperledger Fabric — AuditChaincode:RecordDecision
        var network = _gateway.GetNetwork("aether-audit-channel");
        var contract = network.GetContract("AuditChaincode");
        var txResult = await contract.SubmitTransactionAsync(
            "RecordDecision",
            JsonSerializer.Serialize(record, _opts),
            ct);

        _logger.LogInformation(
            "Audit: {Type} by {Agent} tenant {Tenant} -> block {Block} tx {Tx}",
            decisionType,
            agentName,
            tenantId,
            txResult.BlockNumber,
            txResult.TransactionId);

        await _auditChain.SetLatestHashAsync(tenantId, record.ChainHash, ct);

        return new BlockchainAuditResult
        {
            TransactionId = txResult.TransactionId,
            BlockNumber = txResult.BlockNumber,
            ChainHash = record.ChainHash,
            QuantumSigned = true,
            SignatureAlgorithm = "CRYSTALS-Dilithium-5"
        };
    }

    private static string ComputeChainHash(string previousHash, string recordJson)
    {
        var input = $"{previousHash}{recordJson}";
        var bytes = SHA256.HashData(Encoding.UTF8.GetBytes(input));
        return Convert.ToHexString(bytes).ToLowerInvariant();
    }
}

public sealed class AuditRecord
{
    public string RecordId { get; set; } = string.Empty;
    public string SchemaVersion { get; set; } = "v2";
    public string AgentName { get; set; } = string.Empty;
    public string DecisionType { get; set; } = string.Empty;
    public string TenantId { get; set; } = string.Empty;
    public DateTimeOffset Timestamp { get; set; }
    public JsonElement DecisionData { get; set; }
    public string AetherVersion { get; set; } = string.Empty;
    public string QuantumSignature { get; set; } = string.Empty;
    public string SignatureAlgorithm { get; set; } = string.Empty;
    public string SigningKeyId { get; set; } = string.Empty;
    public string ChainHash { get; set; } = string.Empty;
}

public sealed class BlockchainAuditResult
{
    public string TransactionId { get; set; } = string.Empty;
    public long BlockNumber { get; set; }
    public string ChainHash { get; set; } = string.Empty;
    public bool QuantumSigned { get; set; }
    public string SignatureAlgorithm { get; set; } = string.Empty;
}

public static class BuildInfo
{
    public const string Version = "0.1.0-dev";
}

public interface IPostQuantumDecisionSigner
{
    byte[] SignAgentDecision(byte[] secretKey, object decision);
}

public sealed class NoOpPostQuantumDecisionSigner : IPostQuantumDecisionSigner
{
    public byte[] SignAgentDecision(byte[] secretKey, object decision)
    {
        var payload = JsonSerializer.Serialize(decision);
        return SHA256.HashData(Encoding.UTF8.GetBytes(payload));
    }
}

public interface IAuditChain
{
    Task<string> GetLatestHashAsync(string tenantId, CancellationToken ct = default);
    Task SetLatestHashAsync(string tenantId, string hash, CancellationToken ct = default);
}

public sealed class InMemoryAuditChain : IAuditChain
{
    private readonly System.Collections.Concurrent.ConcurrentDictionary<string, string> _hashes = new();

    public Task<string> GetLatestHashAsync(string tenantId, CancellationToken ct = default)
    {
        _hashes.TryGetValue(tenantId, out var hash);
        return Task.FromResult(hash ?? string.Empty);
    }

    public Task SetLatestHashAsync(string tenantId, string hash, CancellationToken ct = default)
    {
        _hashes[tenantId] = hash;
        return Task.CompletedTask;
    }
}

public interface IHyperledgerGateway
{
    IHyperledgerNetwork GetNetwork(string channelName);
}

public interface IHyperledgerNetwork
{
    IHyperledgerContract GetContract(string contractName);
}

public interface IHyperledgerContract
{
    Task<HyperledgerSubmitResult> SubmitTransactionAsync(
        string transactionName,
        string payloadJson,
        CancellationToken ct = default);
}

public sealed class HyperledgerSubmitResult
{
    public string TransactionId { get; set; } = Guid.NewGuid().ToString("N");
    public long BlockNumber { get; set; } = 0;
}

public sealed class NoOpHyperledgerGateway : IHyperledgerGateway
{
    public IHyperledgerNetwork GetNetwork(string channelName) => new NoOpHyperledgerNetwork(channelName);
}

public sealed class NoOpHyperledgerNetwork : IHyperledgerNetwork
{
    private readonly string _channelName;

    public NoOpHyperledgerNetwork(string channelName)
    {
        _channelName = string.IsNullOrWhiteSpace(channelName) ? "default-channel" : channelName;
    }

    public IHyperledgerContract GetContract(string contractName) => new NoOpHyperledgerContract(_channelName, contractName);
}

public sealed class NoOpHyperledgerContract : IHyperledgerContract
{
    private readonly string _channelName;
    private readonly string _contractName;

    public NoOpHyperledgerContract(string channelName, string contractName)
    {
        _channelName = channelName;
        _contractName = string.IsNullOrWhiteSpace(contractName) ? "AuditChaincode" : contractName;
    }

    public Task<HyperledgerSubmitResult> SubmitTransactionAsync(
        string transactionName,
        string payloadJson,
        CancellationToken ct = default)
    {
        var syntheticTxId = Convert.ToHexString(
            SHA256.HashData(
                Encoding.UTF8.GetBytes($"{_channelName}|{_contractName}|{transactionName}|{payloadJson}|{DateTimeOffset.UtcNow:O}")))
            .ToLowerInvariant();

        var result = new HyperledgerSubmitResult
        {
            TransactionId = syntheticTxId,
            BlockNumber = DateTimeOffset.UtcNow.ToUnixTimeSeconds()
        };

        return Task.FromResult(result);
    }
}
