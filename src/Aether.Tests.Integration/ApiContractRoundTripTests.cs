using System.Text.Json;
using Aether.Models.Connectors;
using Aether.Models.Intelligence;
using Aether.Models.Teams;
using Aether.Models.UseCases;
using Xunit;

namespace Aether.Tests.Integration;

public sealed class ApiContractRoundTripTests
{
    private static readonly JsonSerializerOptions WebJson = new(JsonSerializerDefaults.Web);

    [Fact]
    public void IntelligenceQueryRequest_RoundTrips_Correctly()
    {
        var original = new IntelligenceQueryRequest(
            Question: "Which customers are at churn risk?",
            Systems: new[] { "Salesforce", "Stripe" },
            Explain: true,
            Tenant: "acme",
            Metadata: new Dictionary<string, string> { ["traceId"] = "abc-123" }
        );

        var json = JsonSerializer.Serialize(original, WebJson);
        var roundTrip = JsonSerializer.Deserialize<IntelligenceQueryRequest>(json, WebJson);

        Assert.NotNull(roundTrip);
        Assert.Equal(original.Question, roundTrip!.Question);
        Assert.Equal(original.Systems, roundTrip.Systems);
        Assert.Equal(original.Explain, roundTrip.Explain);
        Assert.Equal(original.Tenant, roundTrip.Tenant);
        Assert.Equal(original.Metadata!["traceId"], roundTrip.Metadata!["traceId"]);
    }

    [Fact]
    public void IntelligenceQueryResponse_RoundTrips_Correctly()
    {
        var original = new IntelligenceQueryResponse(
            Answer: "Stub answer",
            Citations: new[]
            {
                new SourceCitationDto("Salesforce", "sf-001", 0.95),
                new SourceCitationDto("Stripe", "st-002", 0.91)
            },
            Reasoning: new[] { "Question received", "Systems consulted", "Stub response generated" },
            Metadata: new Dictionary<string, string> { ["mode"] = "stub" }
        );

        var json = JsonSerializer.Serialize(original, WebJson);
        var roundTrip = JsonSerializer.Deserialize<IntelligenceQueryResponse>(json, WebJson);

        Assert.NotNull(roundTrip);
        Assert.Equal(original.Answer, roundTrip!.Answer);
        Assert.Equal(2, roundTrip.Citations!.Count);
        Assert.Equal("Salesforce", roundTrip.Citations[0].System);
        Assert.Equal("sf-001", roundTrip.Citations[0].Reference);
        Assert.Equal(0.95, roundTrip.Citations[0].Score);
        Assert.Equal(3, roundTrip.Reasoning!.Count);
        Assert.Equal("stub", roundTrip.Metadata!["mode"]);
    }

    [Fact]
    public void IncidentCommandInvokeRequest_RoundTrips_Correctly()
    {
        var original = new IncidentCommandInvokeRequest(
            IncidentId: "INC0123456",
            AutoDeploy: true,
            Tenant: "acme",
            Metadata: new Dictionary<string, string> { ["source"] = "sdk-test" }
        );

        var json = JsonSerializer.Serialize(original, WebJson);
        var roundTrip = JsonSerializer.Deserialize<IncidentCommandInvokeRequest>(json, WebJson);

        Assert.NotNull(roundTrip);
        Assert.Equal(original.IncidentId, roundTrip!.IncidentId);
        Assert.Equal(original.AutoDeploy, roundTrip.AutoDeploy);
        Assert.Equal(original.Tenant, roundTrip.Tenant);
        Assert.Equal("sdk-test", roundTrip.Metadata!["source"]);
    }

    [Fact]
    public void IncidentCommandInvokeResponse_RoundTrips_Correctly()
    {
        var original = new IncidentCommandInvokeResponse(
            IncidentId: "INC0123456",
            Status: "resolved",
            IterationCount: 1,
            DeployedFix: true,
            ResolutionSummary: "Stub resolved the issue.",
            Actions: new[] { "diagnose", "apply-fix", "verify", "resolve" },
            Metadata: new Dictionary<string, string> { ["mode"] = "stub" }
        );

        var json = JsonSerializer.Serialize(original, WebJson);
        var roundTrip = JsonSerializer.Deserialize<IncidentCommandInvokeResponse>(json, WebJson);

        Assert.NotNull(roundTrip);
        Assert.Equal(original.IncidentId, roundTrip!.IncidentId);
        Assert.Equal(original.Status, roundTrip.Status);
        Assert.Equal(original.IterationCount, roundTrip.IterationCount);
        Assert.Equal(original.DeployedFix, roundTrip.DeployedFix);
        Assert.Equal(original.ResolutionSummary, roundTrip.ResolutionSummary);
        Assert.Equal(4, roundTrip.Actions!.Count);
        Assert.Equal("stub", roundTrip.Metadata!["mode"]);
    }

    [Fact]
    public void CreateSapMaintenanceOrderRequest_RoundTrips_Correctly()
    {
        var original = new CreateSapMaintenanceOrderRequest
        {
            EquipmentId = "MIXER-17",
            Plant = "1000",
            OrderType = "PM01",
            Priority = "1",
            ShortText = "Bearing anomaly detected",
            LongText = "Vibration and temperature exceeded threshold.",
            WorkCentre = "MAINT"
        };

        var json = JsonSerializer.Serialize(original, WebJson);
        var roundTrip = JsonSerializer.Deserialize<CreateSapMaintenanceOrderRequest>(json, WebJson);

        Assert.NotNull(roundTrip);
        Assert.Equal(original.EquipmentId, roundTrip!.EquipmentId);
        Assert.Equal(original.Plant, roundTrip.Plant);
        Assert.Equal(original.OrderType, roundTrip.OrderType);
        Assert.Equal(original.Priority, roundTrip.Priority);
        Assert.Equal(original.ShortText, roundTrip.ShortText);
        Assert.Equal(original.LongText, roundTrip.LongText);
        Assert.Equal(original.WorkCentre, roundTrip.WorkCentre);
    }

    [Fact]
    public void CreateSapMaintenanceOrderResponse_RoundTrips_Correctly()
    {
        var original = new CreateSapMaintenanceOrderResponse
        {
            OrderId = "PM-20260417193000",
            Status = "created",
            Plant = "1000",
            Priority = "1",
            ShortText = "Bearing anomaly detected",
            Metadata = new Dictionary<string, string>
            {
                ["mode"] = "stub",
                ["connector"] = "sap"
            }
        };

        var json = JsonSerializer.Serialize(original, WebJson);
        var roundTrip = JsonSerializer.Deserialize<CreateSapMaintenanceOrderResponse>(json, WebJson);

        Assert.NotNull(roundTrip);
        Assert.Equal(original.OrderId, roundTrip!.OrderId);
        Assert.Equal(original.Status, roundTrip.Status);
        Assert.Equal(original.Plant, roundTrip.Plant);
        Assert.Equal(original.Priority, roundTrip.Priority);
        Assert.Equal(original.ShortText, roundTrip.ShortText);
        Assert.Equal("sap", roundTrip.Metadata!["connector"]);
    }

    [Fact]
    public void MaDueDiligenceRequest_RoundTrips_Correctly()
    {
        var original = new MaDueDiligenceRequest
        {
            Documents = new[] { "doc1.pdf", "doc2.pdf" },
            TargetSystems = new[] { "SAP", "Dynamics", "Workday" },
            OutputFormat = "executive_brief"
        };

        var json = JsonSerializer.Serialize(original, WebJson);
        var roundTrip = JsonSerializer.Deserialize<MaDueDiligenceRequest>(json, WebJson);

        Assert.NotNull(roundTrip);
        Assert.Equal(2, roundTrip!.Documents.Count);
        Assert.Equal(3, roundTrip.TargetSystems.Count);
        Assert.Equal("executive_brief", roundTrip.OutputFormat);
    }

    [Fact]
    public void MaDueDiligenceResponse_RoundTrips_Correctly()
    {
        var original = new MaDueDiligenceResponse
        {
            Status = "completed",
            OutputFormat = "executive_brief",
            DocumentCount = 2,
            EstimatedDurationMinutes = 45,
            ExecutiveSummary = "Stub due diligence summary.",
            TargetSystems = new[] { "SAP", "Dynamics", "Workday" },
            Risks = new[]
            {
                "ERP integration complexity identified.",
                "Identity migration risk identified."
            },
            Metadata = new Dictionary<string, string>
            {
                ["mode"] = "stub",
                ["route"] = "ma-due-diligence"
            }
        };

        var json = JsonSerializer.Serialize(original, WebJson);
        var roundTrip = JsonSerializer.Deserialize<MaDueDiligenceResponse>(json, WebJson);

        Assert.NotNull(roundTrip);
        Assert.Equal(original.Status, roundTrip!.Status);
        Assert.Equal(original.OutputFormat, roundTrip.OutputFormat);
        Assert.Equal(original.DocumentCount, roundTrip.DocumentCount);
        Assert.Equal(original.EstimatedDurationMinutes, roundTrip.EstimatedDurationMinutes);
        Assert.Equal(original.ExecutiveSummary, roundTrip.ExecutiveSummary);
        Assert.Equal(3, roundTrip.TargetSystems.Count);
        Assert.Equal(2, roundTrip.Risks.Count);
        Assert.Equal("ma-due-diligence", roundTrip.Metadata!["route"]);
    }
}