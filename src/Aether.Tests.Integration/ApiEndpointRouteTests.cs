using System.Linq;
using Aether.API.Endpoints;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Routing;
using Xunit;

namespace Aether.Tests.Integration;

public sealed class ApiEndpointRouteTests
{
    [Fact]
    public void IntelligenceEndpoints_Register_Expected_Route()
    {
        var builder = WebApplication.CreateBuilder();
        var app = builder.Build();

        app.MapIntelligenceEndpoints();

        var patterns = app.DataSources
            .SelectMany(ds => ds.Endpoints)
            .OfType<RouteEndpoint>()
            .Select(e => e.RoutePattern.RawText)
            .ToList();

        Assert.Contains("/v1/intelligence/query", patterns);
    }

    [Fact]
    public void IncidentCommandEndpoints_Register_Expected_Route()
    {
        var builder = WebApplication.CreateBuilder();
        var app = builder.Build();

        app.MapIncidentCommandEndpoints();

        var patterns = app.DataSources
            .SelectMany(ds => ds.Endpoints)
            .OfType<RouteEndpoint>()
            .Select(e => e.RoutePattern.RawText)
            .ToList();

        Assert.Contains("/v1/teams/incident-command/invoke", patterns);
    }

    [Fact]
    public void ConnectorEndpoints_Register_Expected_Route()
    {
        var builder = WebApplication.CreateBuilder();
        var app = builder.Build();

        app.MapConnectorEndpoints();

        var patterns = app.DataSources
            .SelectMany(ds => ds.Endpoints)
            .OfType<RouteEndpoint>()
            .Select(e => e.RoutePattern.RawText)
            .ToList();

        Assert.Contains("/v1/connectors/sap/maintenance-orders", patterns);
    }

    [Fact]
    public void UseCaseEndpoints_Register_Expected_Route()
    {
        var builder = WebApplication.CreateBuilder();
        var app = builder.Build();

        app.MapUseCasesEndpoints();

        var patterns = app.DataSources
            .SelectMany(ds => ds.Endpoints)
            .OfType<RouteEndpoint>()
            .Select(e => e.RoutePattern.RawText)
            .ToList();

        Assert.Contains("/v1/use-cases/ma-due-diligence", patterns);
    }
}