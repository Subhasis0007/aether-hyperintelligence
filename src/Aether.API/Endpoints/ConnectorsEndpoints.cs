using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Routing;

namespace Aether.API.Endpoints;

internal sealed record CreateSapMaintenanceOrderRequest(
    string? EquipmentId,
    string Plant,
    string OrderType,
    string Priority,
    string ShortText,
    string LongText,
    string WorkCentre
);

internal sealed record CreateSapMaintenanceOrderResponse(
    string OrderId,
    string Status,
    string Plant,
    string Priority,
    string ShortText,
    IDictionary<string, string>? Metadata = null
);

internal static class ConnectorsEndpoints
{
    public static IEndpointRouteBuilder MapConnectorEndpoints(this IEndpointRouteBuilder app)
    {
        app.MapPost("/v1/connectors/sap/maintenance-orders", async (CreateSapMaintenanceOrderRequest request) =>
        {
            await Task.CompletedTask;

            var orderId = $"PM-{DateTimeOffset.UtcNow:yyyyMMddHHmmss}";

            var response = new CreateSapMaintenanceOrderResponse(
                OrderId: orderId,
                Status: "created",
                Plant: request.Plant,
                Priority: request.Priority,
                ShortText: request.ShortText,
                Metadata: new Dictionary<string, string>
                {
                    ["mode"] = "stub",
                    ["connector"] = "sap",
                    ["order_type"] = request.OrderType,
                    ["equipment_id"] = request.EquipmentId ?? string.Empty,
                    ["work_centre"] = request.WorkCentre
                }
            );

            return Results.Ok(response);
        })
        .WithName("CreateSapMaintenanceOrder")
        .WithTags("Connectors");

        return app;
    }
}