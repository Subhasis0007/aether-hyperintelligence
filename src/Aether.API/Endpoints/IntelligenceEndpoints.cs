using Aether.Models.Intelligence;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Routing;

namespace Aether.API.Endpoints;

/// <summary>
/// Registers intelligence-related API endpoints.
/// </summary>
public static class IntelligenceEndpoints
{
    /// <summary>
    /// Maps the intelligence query endpoint.
    /// </summary>
    /// <param name="app">The endpoint route builder.</param>
    /// <returns>The endpoint route builder for chaining.</returns>
    public static IEndpointRouteBuilder MapIntelligenceEndpoints(this IEndpointRouteBuilder app)
    {
        app.MapPost("/v1/intelligence/query", (IntelligenceQueryRequest request) =>
        {
            var systems = request.Systems is { Count: > 0 }
                ? request.Systems
                : Array.Empty<string>();

            var citations = new List<SourceCitationDto>();

            foreach (var system in systems)
            {
                citations.Add(new SourceCitationDto(
                    system,
                    $"stub-{system.ToLowerInvariant()}-001",
                    0.95
                ));
            }

            var reasoning = request.Explain
                ? new List<string>
                {
                    $"Question received: {request.Question}",
                    $"Systems consulted: {(systems.Count > 0 ? string.Join(", ", systems) : "none")}",
                    "Response generated from current stub endpoint."
                }
                : null;

            var response = new IntelligenceQueryResponse(
                Answer: $"Stub answer for question: {request.Question}",
                Citations: citations,
                Reasoning: reasoning,
                Metadata: new Dictionary<string, string>
                {
                    ["mode"] = "stub",
                    ["tenant"] = request.Tenant ?? string.Empty
                }
            );

            return Results.Ok(response);
        })
        .WithName("IntelligenceQuery")
        .WithTags("Intelligence");

        return app;
    }
}