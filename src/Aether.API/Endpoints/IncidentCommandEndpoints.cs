using Aether.Models.Teams;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Routing;

namespace Aether.API.Endpoints;

internal static class IncidentCommandEndpoints
{
    public static IEndpointRouteBuilder MapIncidentCommandEndpoints(this IEndpointRouteBuilder app)
    {
        app.MapPost("/v1/teams/incident-command/invoke", async (IncidentCommandInvokeRequest request) =>
        {
            await Task.CompletedTask;

            var response = new IncidentCommandInvokeResponse(
                IncidentId: request.IncidentId,
                Status: request.AutoDeploy ? "resolved" : "proposed",
                IterationCount: 1,
                DeployedFix: request.AutoDeploy,
                ResolutionSummary: request.AutoDeploy
                    ? "Stub incident workflow resolved the issue with automatic remediation."
                    : "Stub incident workflow generated a proposed remediation without deployment.",
                Actions: request.AutoDeploy
                    ? new List<string> { "diagnose", "apply-fix", "verify", "resolve" }
                    : new List<string> { "diagnose", "propose-fix" },
                Metadata: new Dictionary<string, string>
                {
                    ["mode"] = "stub",
                    ["auto_deploy_requested"] = request.AutoDeploy.ToString(),
                    ["route"] = "incident-command",
                    ["tenant"] = request.Tenant ?? string.Empty
                }
            );

            return Results.Ok(response);
        })
        .WithName("IncidentCommandInvoke")
        .WithTags("Teams");

        return app;
    }
}