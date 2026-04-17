using System.Text.Json;
using Aether.Models.Connectors;
using Aether.Models.Intelligence;
using Aether.Models.Teams;
using Aether.Models.UseCases;
using Xunit;

namespace Aether.Tests.Integration;

public sealed class ContractSerializationTests
{
    private static readonly JsonSerializerOptions WebJson = new(JsonSerializerDefaults.Web);

    [Fact]
    public void IntelligenceQueryRequest_Serializes_To_Expected_Web_Contract()
    {
        var request = new IntelligenceQueryRequest(
            Question: "Which customers are at churn risk?",
            Systems: new[] { "Salesforce", "Stripe" },
            Explain: true,
            Tenant: "acme",
            Metadata: new Dictionary<string, string> { ["traceId"] = "abc-123" }
        );

        var json = JsonSerializer.Serialize(request, WebJson);

        Assert.Contains(@"""question"":""Which customers are at churn risk?""", json);
        Assert.Contains(@"""systems"":[""Salesforce"",""Stripe""]", json);
        Assert.Contains(@"""explain"":true", json);
        Assert.Contains(@"""tenant"":""acme""", json);
        Assert.Contains(@"""metadata"":{""traceId"":""abc-123""}", json);
    }

    [Fact]
    public void IncidentCommandInvokeRequest_Serializes_To_Expected_Web_Contract()
    {
        var request = new IncidentCommandInvokeRequest(
            IncidentId: "INC0123456",
            AutoDeploy: true,
            Tenant: "acme",
            Metadata: new Dictionary<string, string> { ["source"] = "sdk-test" }
        );

        var json = JsonSerializer.Serialize(request, WebJson);

        Assert.Contains(@"""incidentId"":""INC0123456""", json);
        Assert.Contains(@"""autoDeploy"":true", json);
        Assert.Contains(@"""tenant"":""acme""", json);
        Assert.Contains(@"""metadata"":{""source"":""sdk-test""}", json);
    }

    [Fact]
    public void CreateSapMaintenanceOrderRequest_Serializes_To_Expected_Web_Contract()
    {
        var request = new CreateSapMaintenanceOrderRequest
        {
            EquipmentId = "MIXER-17",
            Plant = "1000",
            OrderType = "PM01",
            Priority = "1",
            ShortText = "Bearing anomaly detected",
            LongText = "Vibration and temperature exceeded threshold.",
            WorkCentre = "MAINT"
        };

        var json = JsonSerializer.Serialize(request, WebJson);

        Assert.Contains(@"""equipmentId"":""MIXER-17""", json);
        Assert.Contains(@"""plant"":""1000""", json);
        Assert.Contains(@"""orderType"":""PM01""", json);
        Assert.Contains(@"""priority"":""1""", json);
        Assert.Contains(@"""shortText"":""Bearing anomaly detected""", json);
        Assert.Contains(@"""longText"":""Vibration and temperature exceeded threshold.""", json);
        Assert.Contains(@"""workCentre"":""MAINT""", json);
    }

    [Fact]
    public void MaDueDiligenceRequest_Serializes_To_Expected_Web_Contract()
    {
        var request = new MaDueDiligenceRequest
        {
            Documents = new[] { "doc1.pdf", "doc2.pdf" },
            TargetSystems = new[] { "SAP", "Dynamics", "Workday" },
            OutputFormat = "executive_brief"
        };

        var json = JsonSerializer.Serialize(request, WebJson);

        Assert.Contains(@"""documents"":[""doc1.pdf"",""doc2.pdf""]", json);
        Assert.Contains(@"""targetSystems"":[""SAP"",""Dynamics"",""Workday""]", json);
        Assert.Contains(@"""outputFormat"":""executive_brief""", json);
    }
}