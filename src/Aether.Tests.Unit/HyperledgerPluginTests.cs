using Aether.Agents.Connectors.Blockchain;
using Aether.Core.WASM;
using Xunit;

namespace Aether.Tests.Unit;

public sealed class HyperledgerPluginTests
{
    [Fact]
    public async Task RecordDecisionAsync_Returns_Audit_Result_For_Valid_Input()
    {
        var plugin = new HyperledgerPlugin();

        var result = await plugin.RecordDecisionAsync(
            agentName: "incident-commander",
            decisionType: "resolve-incident",
            decisionJson: "{\"severity\":\"high\"}",
            tenantId: "acme");

        Assert.NotNull(result);
        Assert.NotEmpty(result.TransactionId);
        Assert.NotEmpty(result.ChainHash);
        Assert.True(result.BlockNumber > 0);
        Assert.True(result.QuantumSigned);
        Assert.Equal("CRYSTALS-Dilithium-5", result.SignatureAlgorithm);
    }

    [Theory]
    [InlineData(null, "resolve-incident", "acme", "agentName")]
    [InlineData("incident-commander", null, "acme", "decisionType")]
    [InlineData("incident-commander", "resolve-incident", null, "tenantId")]
    [InlineData(" ", "resolve-incident", "acme", "agentName")]
    [InlineData("incident-commander", " ", "acme", "decisionType")]
    [InlineData("incident-commander", "resolve-incident", " ", "tenantId")]
    public async Task RecordDecisionAsync_Rejects_Missing_Required_Arguments(
        string? agentName,
        string? decisionType,
        string? tenantId,
        string expectedParamName)
    {
        var plugin = new HyperledgerPlugin();

        var exception = await Assert.ThrowsAsync<ArgumentException>(() => plugin.RecordDecisionAsync(
            agentName: agentName!,
            decisionType: decisionType!,
            decisionJson: "{}",
            tenantId: tenantId!));

        Assert.Equal(expectedParamName, exception.ParamName);
    }

    [Fact]
    public async Task InMemoryAuditChain_Persists_Hash_By_Tenant()
    {
        var chain = new InMemoryAuditChain();

        await chain.SetLatestHashAsync("acme", "hash-123");

        var latestHash = await chain.GetLatestHashAsync("acme");

        Assert.Equal("hash-123", latestHash);
    }

    [Fact]
    public void NoOpPostQuantumDecisionSigner_Is_Deterministic_For_Same_Payload()
    {
        var signer = new NoOpPostQuantumDecisionSigner();
        var decision = new { Agent = "incident-commander", Status = "resolved" };

        var firstSignature = signer.SignAgentDecision(Array.Empty<byte>(), decision);
        var secondSignature = signer.SignAgentDecision(Array.Empty<byte>(), decision);

        Assert.Equal(firstSignature, secondSignature);
        Assert.NotEmpty(firstSignature);
    }

    [Fact]
    public async Task NoOpHyperledgerGateway_SubmitTransaction_Returns_Synthetic_Result()
    {
        var gateway = new NoOpHyperledgerGateway();
        var network = gateway.GetNetwork("aether-audit-channel");
        var contract = network.GetContract("AuditChaincode");

        var result = await contract.SubmitTransactionAsync("RecordDecision", "{\"status\":\"ok\"}");

        Assert.NotNull(result);
        Assert.NotEmpty(result.TransactionId);
        Assert.True(result.BlockNumber > 0);
    }

    [Theory]
    [InlineData(new byte[] { 1 }, new byte[] { 2 }, true)]
    [InlineData(new byte[] { 1 }, new byte[0], false)]
    [InlineData(new byte[0], new byte[] { 2 }, false)]
    public void NoOpPostQuantumModuleVerifier_Requires_Module_Bytes_And_Signature(
        byte[] moduleBytes,
        byte[] signature,
        bool expected)
    {
        var verifier = new NoOpPostQuantumModuleVerifier();

        var isValid = verifier.VerifyModuleSignature(new byte[] { 9 }, moduleBytes, signature);

        Assert.Equal(expected, isValid);
    }
}