using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Security;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Wasmtime;

namespace Aether.Core.WASM;

public interface IWasmAgentRunner
{
    Task<WasmAgentResult> RunAsync(
        WasmAgentModule module,
        AgentTask task,
        WasmCapabilitySet caps,
        CancellationToken ct = default);
}

public sealed class WasmAgentRunner : IWasmAgentRunner
{
    private readonly IPostQuantumModuleVerifier _pq;
    private readonly ILogger<WasmAgentRunner> _log;

    public WasmAgentRunner()
        : this(new NoOpPostQuantumModuleVerifier(), NullLogger<WasmAgentRunner>.Instance)
    {
    }

    public WasmAgentRunner(
        IPostQuantumModuleVerifier pq,
        ILogger<WasmAgentRunner> log)
    {
        _pq = pq;
        _log = log;
    }

    public async Task<WasmAgentResult> RunAsync(
        WasmAgentModule module,
        AgentTask task,
        WasmCapabilitySet caps,
        CancellationToken ct = default)
    {
        using var activity = Activity.Current?.Source.StartActivity("wasm.agent.run")
                            ?? new Activity("wasm.agent.run").Start();

        activity?.SetTag("wasm.module", module.Name);
        activity?.SetTag("wasm.tenant", task.TenantId);

        // ── Step 1: Verify post-quantum publisher signature ────────────
        var moduleBytes = await File.ReadAllBytesAsync(module.Path, ct);
        if (!_pq.VerifyModuleSignature(module.PublisherPublicKey, moduleBytes, module.Signature))
        {
            throw new SecurityException($"WASM module '{module.Name}' signature invalid.");
        }

        _log.LogInformation("WASM module {Name} PQ-signature verified", module.Name);

        // ── Step 2: Create Wasmtime engine / module / linker / store ───
        using var engine = new Engine();
        using var wasmModule = Module.FromBytes(engine, module.Name, moduleBytes);
        using var linker = new Linker(engine);
        using var store = new Store(engine);

        // Import validation (capability gate)
        ValidateImportsAgainstCapabilities(wasmModule, caps);

        // NOTE:
        // This first scaffold intentionally executes only self-contained modules.
        // If imports are present, we fail fast with a clear message so the build stays clean.
        if (wasmModule.Imports.Count > 0)
        {
            var importList = string.Join(", ",
                wasmModule.Imports.Select(i => $"{i.ModuleName}/{i.Name}"));

            return new WasmAgentResult(
                Success: false,
                Output: $"Module '{module.Name}' requires host imports not yet bound in scaffold: {importList}",
                FuelUsed: 0,
                ModuleName: module.Name);
        }

        // ── Step 3: Instantiate and invoke exported action ──────────────
        var sw = Stopwatch.StartNew();

        var instance = linker.Instantiate(store, wasmModule);

        // Supported first-pass exports:
        // - aether_run()
        // - run()
        var aetherRun = instance.GetAction("aether_run") ?? instance.GetAction("run");
        if (aetherRun is null)
        {
            return new WasmAgentResult(
                Success: false,
                Output: $"No supported exported action found. Expected 'aether_run' or 'run'.",
                FuelUsed: 0,
                ModuleName: module.Name);
        }

        aetherRun();

        sw.Stop();

        // Synthetic fuel model for first scaffold:
        // Prompt target said ~100M units ≈ 80ms, so map elapsed ms proportionally.
        ulong syntheticFuelUsed = ComputeSyntheticFuel(sw.Elapsed, caps.MaxFuelUnits);

        activity?.SetTag("wasm.fuel_used", syntheticFuelUsed);
        activity?.SetTag("wasm.elapsed_ms", sw.Elapsed.TotalMilliseconds);

        return new WasmAgentResult(
            Success: true,
            Output: JsonSerializer.Serialize(new
            {
                task.TaskName,
                task.TenantId,
                status = "executed",
                elapsed_ms = sw.Elapsed.TotalMilliseconds
            }),
            FuelUsed: syntheticFuelUsed,
            ModuleName: module.Name);
    }

    private static void ValidateImportsAgainstCapabilities(Module wasmModule, WasmCapabilitySet caps)
    {
        foreach (var import in wasmModule.Imports)
        {
            var mod = import.ModuleName ?? string.Empty;
            var name = import.Name ?? string.Empty;

            if (mod != "aether")
            {
                throw new SecurityException(
                    $"Import '{mod}/{name}' is not allowed. Only 'aether/*' imports are permitted.");
            }

            if (name.Equals("kg_query", StringComparison.Ordinal))
            {
                if (!caps.CanReadKnowledgeGraph)
                {
                    throw new SecurityException("Module imports 'aether/kg_query' but capability is denied.");
                }
                continue;
            }

            if (name.Equals("connector_read", StringComparison.Ordinal))
            {
                if (!caps.CanReadConnector)
                {
                    throw new SecurityException("Module imports 'aether/connector_read' but capability is denied.");
                }
                continue;
            }

            throw new SecurityException(
                $"Import 'aether/{name}' is not allowed. Allowed imports: kg_query, connector_read.");
        }
    }

    private static ulong ComputeSyntheticFuel(TimeSpan elapsed, ulong maxFuelUnits)
    {
        // 100M units ≈ 80ms from your design note:
        // units_per_ms = 100_000_000 / 80 = 1_250_000
        const double unitsPerMs = 1_250_000d;
        var used = (ulong)Math.Min(maxFuelUnits, Math.Max(0, elapsed.TotalMilliseconds * unitsPerMs));
        return used;
    }
}

public sealed record WasmAgentModule(
    string Name,
    string Path,
    byte[] PublisherPublicKey,
    byte[] Signature);

public sealed record AgentTask(
    string TaskName,
    string TenantId,
    int TenantIdAsInt,
    Dictionary<string, object?> Payload);

public sealed record WasmCapabilitySet(
    bool CanReadKnowledgeGraph,
    bool CanReadConnector,
    ulong MaxFuelUnits);

public sealed record WasmAgentResult(
    bool Success,
    string Output,
    ulong FuelUsed,
    string ModuleName);

public interface IPostQuantumModuleVerifier
{
    bool VerifyModuleSignature(byte[] publisherPublicKey, byte[] moduleBytes, byte[] signature);
}

public sealed class NoOpPostQuantumModuleVerifier : IPostQuantumModuleVerifier
{
    public bool VerifyModuleSignature(byte[] publisherPublicKey, byte[] moduleBytes, byte[] signature)
    {
        // Scaffold verifier: accept non-empty signature only.
        // Replace with real Dilithium/SPHINCS+ verification later.
        return signature is { Length: > 0 } && moduleBytes is { Length: > 0 };
    }
}
