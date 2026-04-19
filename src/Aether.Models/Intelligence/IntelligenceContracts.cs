namespace Aether.Models.Intelligence;

/// <summary>
/// Request contract for an intelligence query against one or more source systems.
/// </summary>
/// <param name="Question">The natural-language question to answer.</param>
/// <param name="Systems">The source systems to consult when generating a response.</param>
/// <param name="Explain">Whether the response should include reasoning details.</param>
/// <param name="Tenant">The tenant identifier associated with the request.</param>
/// <param name="Metadata">Optional metadata to attach to the request.</param>
public sealed record IntelligenceQueryRequest(
    string Question,
    IReadOnlyList<string>? Systems = null,
    bool Explain = false,
    string? Tenant = null,
    IDictionary<string, string>? Metadata = null
);

/// <summary>
/// Describes a source citation included in an intelligence response.
/// </summary>
/// <param name="System">The source system that produced the cited information.</param>
/// <param name="Reference">The source-specific reference or identifier.</param>
/// <param name="Score">A confidence or relevance score for the citation.</param>
public sealed record SourceCitationDto(
    string System,
    string Reference,
    double Score = 1.0
);

/// <summary>
/// Response contract for an intelligence query.
/// </summary>
/// <param name="Answer">The answer returned for the query.</param>
/// <param name="Citations">Optional source citations supporting the answer.</param>
/// <param name="Reasoning">Optional reasoning steps explaining the answer.</param>
/// <param name="Metadata">Optional metadata associated with the response.</param>
public sealed record IntelligenceQueryResponse(
    string Answer,
    IReadOnlyList<SourceCitationDto>? Citations = null,
    IReadOnlyList<string>? Reasoning = null,
    IDictionary<string, string>? Metadata = null
);