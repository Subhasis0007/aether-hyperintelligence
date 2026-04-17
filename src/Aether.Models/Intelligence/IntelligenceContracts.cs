namespace Aether.Models.Intelligence;

public sealed record IntelligenceQueryRequest(
    string Question,
    IReadOnlyList<string>? Systems = null,
    bool Explain = false,
    string? Tenant = null,
    IDictionary<string, string>? Metadata = null
);

public sealed record SourceCitationDto(
    string System,
    string Reference,
    double Score = 1.0
);

public sealed record IntelligenceQueryResponse(
    string Answer,
    IReadOnlyList<SourceCitationDto>? Citations = null,
    IReadOnlyList<string>? Reasoning = null,
    IDictionary<string, string>? Metadata = null
);