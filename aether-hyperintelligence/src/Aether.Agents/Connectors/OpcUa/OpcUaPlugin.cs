using System;
using System.ComponentModel;
using System.Diagnostics;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Opc.Ua;
using Opc.Ua.Client;
using Opc.Ua.Configuration;

namespace Aether.Agents.Connectors.OpcUa;

public sealed class OpcUaPlugin
{
    private readonly ActivitySource _tracer = new("Aether.Agents.OPCUA");
    private readonly string _tenantId;
    private readonly OpcUaPluginConfig _config;
    private readonly INatsPublisher _nats;

    public OpcUaPlugin()
        : this("default-tenant", new OpcUaPluginConfig(), new NoOpNatsPublisher())
    {
    }

    public OpcUaPlugin(string tenantId, OpcUaPluginConfig config, INatsPublisher nats)
    {
        _tenantId = tenantId;
        _config = config;
        _nats = nats;
    }

    [KernelFunction("opcua_read_node")]
    [Description("Read a real-time value from an OPC-UA node on a factory PLC or SCADA system.")]
    public async Task<OpcUaReadResult> ReadNodeAsync(
        [Description("OPC-UA NodeId, e.g. ns=2;s=Boiler.Temperature")] string nodeId,
        [Description("Optional OPC-UA server URL. Defaults to tenant configured endpoint.")] string? serverUrl = null,
        CancellationToken ct = default)
    {
        using var activity = _tracer.StartActivity("opcua.read");
        activity?.SetTag("aether.node_id", nodeId);
        activity?.SetTag("aether.tenant", _tenantId);

        var targetUrl = serverUrl ?? _config.DefaultServerUrl;
        var appConfig = await BuildApplicationConfigAsync(ct);

        using var discoveryClient = await DiscoveryClient.CreateAsync(new Uri(targetUrl), null);
        var endpoints = await discoveryClient.GetEndpointsAsync(null);

        var endpointDescription = CoreClientUtils.SelectEndpoint(
            appConfig,
            new Uri(targetUrl),
            endpoints,
            true,
            null!);

        var endpoint = new ConfiguredEndpoint(
            null,
            endpointDescription,
            EndpointConfiguration.Create(appConfig));

        ISessionFactory sessionFactory = new DefaultSessionFactory(null!);
        using var session = await sessionFactory.CreateAsync(
            configuration: appConfig,
            endpoint: endpoint,
            updateBeforeConnect: false,
            checkDomain: false,
            sessionName: $"AETHER-{_tenantId}",
            sessionTimeout: 60_000,
            identity: new UserIdentity(),
            preferredLocales: null,
            ct: ct);

        var reading = await session.ReadValueAsync(NodeId.Parse(nodeId), ct);

        if (StatusCode.IsBad(reading.StatusCode))
        {
            throw new ServiceResultException(
                reading.StatusCode,
                $"OPC-UA read failed for node {nodeId}: {reading.StatusCode}");
        }

        await _nats.PublishAsync(
            "aether.iot.opcua",
            new OpcUaReadingEvent
            {
                NodeId = nodeId,
                Value = reading.Value?.ToString() ?? string.Empty,
                StatusCode = reading.StatusCode.Code,
                SourceTime = reading.SourceTimestamp,
                TenantId = _tenantId
            },
            ct);

        return new OpcUaReadResult(
            nodeId,
            reading.Value?.ToString(),
            reading.StatusCode.Code,
            reading.ServerTimestamp);
    }

    private static async Task<ApplicationConfiguration> BuildApplicationConfigAsync(CancellationToken ct)
    {
        var config = new ApplicationConfiguration
        {
            ApplicationName = "AETHER OPC-UA Client",
            ApplicationUri = $"urn:{Environment.MachineName}:AETHER:OPCUA",
            ApplicationType = ApplicationType.Client,
            SecurityConfiguration = new SecurityConfiguration
            {
                ApplicationCertificate = new CertificateIdentifier(),
                AutoAcceptUntrustedCertificates = true,
                RejectSHA1SignedCertificates = false,
                MinimumCertificateKeySize = 2048
            },
            TransportQuotas = new TransportQuotas
            {
                OperationTimeout = 15_000
            },
            ClientConfiguration = new ClientConfiguration
            {
                DefaultSessionTimeout = 60_000
            },
            TraceConfiguration = new TraceConfiguration()
        };

        await config.ValidateAsync(ApplicationType.Client, ct);

        if (config.SecurityConfiguration.AutoAcceptUntrustedCertificates)
        {
            config.CertificateValidator.CertificateValidation += (_, e) => e.Accept = true;
        }

        ct.ThrowIfCancellationRequested();
        return config;
    }
}

public sealed class OpcUaPluginConfig
{
    public string DefaultServerUrl { get; set; } = "opc.tcp://localhost:4840";
}

public sealed record OpcUaReadResult(
    string NodeId,
    string? Value,
    uint StatusCode,
    DateTime ServerTimestamp);

public sealed class OpcUaReadingEvent
{
    public string NodeId { get; set; } = string.Empty;
    public string Value { get; set; } = string.Empty;
    public uint StatusCode { get; set; }
    public DateTime SourceTime { get; set; }
    public string TenantId { get; set; } = string.Empty;
}

public interface INatsPublisher
{
    Task PublishAsync(string subject, object data, CancellationToken cancellationToken = default);
}

public sealed class NoOpNatsPublisher : INatsPublisher
{
    public Task PublishAsync(string subject, object data, CancellationToken cancellationToken = default)
        => Task.CompletedTask;
}
