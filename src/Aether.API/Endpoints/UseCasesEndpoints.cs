using Aether.Models.UseCases;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Routing;

namespace Aether.API.Endpoints;

internal static class UseCasesEndpoints
{
    public static IEndpointRouteBuilder MapUseCasesEndpoints(this IEndpointRouteBuilder app)
    {
        app.MapPost("/v1/use-cases/ma-due-diligence", async (MaDueDiligenceRequest request) =>
        {
            await Task.CompletedTask;

            var response = new MaDueDiligenceResponse
            {
                Status = "completed",
                OutputFormat = request.OutputFormat,
                DocumentCount = request.Documents.Count,
                EstimatedDurationMinutes = 45,
                ExecutiveSummary = $"Stub due diligence summary generated for {request.Documents.Count} documents across {request.TargetSystems.Count} target systems.",
                TargetSystems = request.TargetSystems,
                Risks = new List<string>
                {
                    "ERP integration complexity identified in stub analysis.",
                    "Identity and access migration risk identified in stub analysis.",
                    "Data model harmonisation required between target systems."
                },
                Metadata = new Dictionary<string, string>
                {
                    ["mode"] = "stub",
                    ["route"] = "ma-due-diligence",
                    ["documents_processed"] = request.Documents.Count.ToString()
                }
            };

            return Results.Ok(response);
        })
        .WithName("MaDueDiligence")
        .WithTags("UseCases");

        return app;
    }
}