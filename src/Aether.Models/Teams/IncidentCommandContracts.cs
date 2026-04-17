namespace Aether.Models.Teams;

/// <summary>
/// Request contract for invoking the incident command workflow.
/// </summary>
public sealed record IncidentCommandInvokeRequest(
    string IncidentId,
    bool AutoDeploy = false,
    string? Tenant = null,
    IDictionary<string, string>? Metadata = null
);

/// <summary>
/// Response contract returned by the incident command workflow.
/// </summary>
public sealed record IncidentCommandInvokeResponse(
    string IncidentId,
    string Status,
    int IterationCount,
    bool DeployedFix,
    string ResolutionSummary,
    IReadOnlyList<string>? Actions = null,
    IDictionary<string, string>? Metadata = null
);