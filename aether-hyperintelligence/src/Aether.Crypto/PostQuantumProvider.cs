using System;
using System.Text.Json;
using LibOQS.NET;

namespace Aether.Crypto;

public sealed class PostQuantumProvider : IDisposable
{
    private readonly JsonSerializerOptions _jsonOpts = new(JsonSerializerDefaults.Web);

    // ── Key Encapsulation: ML-KEM-1024 (NIST-standardized successor to Kyber-1024) ──
    public (byte[] publicKey, byte[] secretKey) GenerateKyberKeypair()
    {
        using var kem = new KemInstance(KemAlgorithm.MlKem1024);
        return kem.GenerateKeypair();
    }

    // Sender encapsulates with recipient public key
    // Returns: ciphertext to send + shared secret
    public (byte[] ciphertext, byte[] sharedSecret) Encapsulate(byte[] recipientPublicKey)
    {
        using var kem = new KemInstance(KemAlgorithm.MlKem1024);
        return kem.Encapsulate(recipientPublicKey);
    }

    public byte[] Decapsulate(byte[] secretKey, byte[] ciphertext)
    {
        using var kem = new KemInstance(KemAlgorithm.MlKem1024);
        return kem.Decapsulate(secretKey, ciphertext);
    }

    // ── Digital Signatures: ML-DSA-87 (NIST-standardized successor to Dilithium-5) ──
    public (byte[] publicKey, byte[] secretKey) GenerateDilithiumKeypair()
    {
        using var sig = new SigInstance(SigAlgorithm.MlDsa87);
        return sig.GenerateKeypair();
    }

    public byte[] SignAgentDecision(byte[] secretKey, AgentDecisionRecord decision)
    {
        using var sig = new SigInstance(SigAlgorithm.MlDsa87);
        var payload = JsonSerializer.SerializeToUtf8Bytes(decision, _jsonOpts);
        return sig.Sign(payload, secretKey);
    }

    public bool VerifyDecision(byte[] publicKey, AgentDecisionRecord decision, byte[] signature)
    {
        using var sig = new SigInstance(SigAlgorithm.MlDsa87);
        var payload = JsonSerializer.SerializeToUtf8Bytes(decision, _jsonOpts);
        return sig.Verify(payload, signature, publicKey);
    }

    public void Dispose()
    {
        // Optional cleanup hook if you want explicit shutdown:
        // LibOqs.Cleanup();
    }
}

public sealed record AgentDecisionRecord(
    string AgentName,
    string DecisionType,
    string TenantId,
    DateTimeOffset Timestamp,
    string PayloadJson);
