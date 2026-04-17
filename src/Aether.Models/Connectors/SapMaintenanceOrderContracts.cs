namespace Aether.Models.Connectors;

/// <summary>
/// Request contract for creating a SAP maintenance order.
/// </summary>
public sealed class CreateSapMaintenanceOrderRequest
{
    /// <summary>
    /// Gets or sets the equipment identifier associated with the maintenance order.
    /// </summary>
    public string? EquipmentId { get; init; }

    /// <summary>
    /// Gets or sets the SAP plant code.
    /// </summary>
    public required string Plant { get; init; }

    /// <summary>
    /// Gets or sets the SAP order type.
    /// </summary>
    public required string OrderType { get; init; }

    /// <summary>
    /// Gets or sets the priority assigned to the maintenance order.
    /// </summary>
    public required string Priority { get; init; }

    /// <summary>
    /// Gets or sets the short text description for the order.
    /// </summary>
    public required string ShortText { get; init; }

    /// <summary>
    /// Gets or sets the long text description for the order.
    /// </summary>
    public required string LongText { get; init; }

    /// <summary>
    /// Gets or sets the work centre responsible for the order.
    /// </summary>
    public required string WorkCentre { get; init; }
}

/// <summary>
/// Response contract returned after creating a SAP maintenance order.
/// </summary>
public sealed class CreateSapMaintenanceOrderResponse
{
    /// <summary>
    /// Gets or sets the generated maintenance order identifier.
    /// </summary>
    public required string OrderId { get; init; }

    /// <summary>
    /// Gets or sets the resulting status of the maintenance order request.
    /// </summary>
    public required string Status { get; init; }

    /// <summary>
    /// Gets or sets the SAP plant code.
    /// </summary>
    public required string Plant { get; init; }

    /// <summary>
    /// Gets or sets the assigned priority.
    /// </summary>
    public required string Priority { get; init; }

    /// <summary>
    /// Gets or sets the short text description for the created order.
    /// </summary>
    public required string ShortText { get; init; }

    /// <summary>
    /// Gets or sets additional metadata for the connector response.
    /// </summary>
    public IDictionary<string, string>? Metadata { get; init; }
}