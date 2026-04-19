namespace Aether.Models.UseCases;

/// <summary>
/// Request contract for running the M&amp;A due diligence use case.
/// </summary>
public sealed class MaDueDiligenceRequest
{
    /// <summary>
    /// Gets or sets the list of documents to analyze.
    /// </summary>
    public required IReadOnlyList<string> Documents { get; init; }

    /// <summary>
    /// Gets or sets the list of target systems in scope for due diligence.
    /// </summary>
    public required IReadOnlyList<string> TargetSystems { get; init; }

    /// <summary>
    /// Gets or sets the requested output format.
    /// </summary>
    public string OutputFormat { get; init; } = "executive_brief";
}

/// <summary>
/// Response contract returned by the M&amp;A due diligence workflow.
/// </summary>
public sealed class MaDueDiligenceResponse
{
    /// <summary>
    /// Gets or sets the resulting workflow status.
    /// </summary>
    public required string Status { get; init; }

    /// <summary>
    /// Gets or sets the output format that was produced.
    /// </summary>
    public required string OutputFormat { get; init; }

    /// <summary>
    /// Gets or sets the number of documents processed.
    /// </summary>
    public int DocumentCount { get; init; }

    /// <summary>
    /// Gets or sets the estimated duration in minutes.
    /// </summary>
    public int EstimatedDurationMinutes { get; init; }

    /// <summary>
    /// Gets or sets the generated executive summary.
    /// </summary>
    public required string ExecutiveSummary { get; init; }

    /// <summary>
    /// Gets or sets the target systems included in the analysis.
    /// </summary>
    public required IReadOnlyList<string> TargetSystems { get; init; }

    /// <summary>
    /// Gets or sets the identified risks.
    /// </summary>
    public required IReadOnlyList<string> Risks { get; init; }

    /// <summary>
    /// Gets or sets optional metadata for the response.
    /// </summary>
    public IDictionary<string, string>? Metadata { get; init; }
}