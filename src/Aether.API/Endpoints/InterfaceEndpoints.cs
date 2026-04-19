using System.Net.WebSockets;
using System.Text;
using System.Text.Json;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Routing;

namespace Aether.API.Endpoints;

internal static class InterfaceEndpoints
{
    public static IEndpointRouteBuilder MapInterfaceEndpoints(this IEndpointRouteBuilder app)
    {
        app.MapPost("/graphql", async (HttpContext context) =>
        {
            var payload = await JsonSerializer.DeserializeAsync<GraphQlRequest>(context.Request.Body)
                ?? new GraphQlRequest();

            var query = payload.Query?.Trim() ?? string.Empty;
            var data = new Dictionary<string, object?>
            {
                ["service"] = "Aether.API",
                ["mode"] = "stub",
                ["query"] = query,
                ["variables"] = payload.Variables ?? new Dictionary<string, object?>(),
                ["message"] = "GraphQL interface is available as a lightweight compatibility stub."
            };

            return Results.Ok(new { data });
        })
        .WithName("GraphQlStub")
        .WithTags("Interfaces");

        app.MapGet("/v1/events/stream", async (HttpContext context) =>
        {
            context.Response.Headers.Append("Content-Type", "text/event-stream");
            context.Response.Headers.Append("Cache-Control", "no-cache");

            for (var i = 1; i <= 3; i++)
            {
                var evt = JsonSerializer.Serialize(new
                {
                    type = "heartbeat",
                    sequence = i,
                    utc = DateTimeOffset.UtcNow
                });

                await context.Response.WriteAsync($"event: heartbeat\n");
                await context.Response.WriteAsync($"data: {evt}\n\n");
                await context.Response.Body.FlushAsync();
                await Task.Delay(350, context.RequestAborted);
            }
        })
        .WithName("ServerSentEvents")
        .WithTags("Interfaces");

        app.Map("/ws", async context =>
        {
            if (!context.WebSockets.IsWebSocketRequest)
            {
                context.Response.StatusCode = StatusCodes.Status400BadRequest;
                await context.Response.WriteAsync("Expected a WebSocket upgrade request.");
                return;
            }

            using var socket = await context.WebSockets.AcceptWebSocketAsync();
            var welcome = Encoding.UTF8.GetBytes("AETHER WebSocket ready. Send any message to echo.");
            await socket.SendAsync(welcome, WebSocketMessageType.Text, true, context.RequestAborted);

            var buffer = new byte[4096];
            while (!context.RequestAborted.IsCancellationRequested && socket.State == WebSocketState.Open)
            {
                var result = await socket.ReceiveAsync(buffer, context.RequestAborted);
                if (result.MessageType == WebSocketMessageType.Close)
                {
                    await socket.CloseAsync(WebSocketCloseStatus.NormalClosure, "Closing", context.RequestAborted);
                    break;
                }

                var incoming = Encoding.UTF8.GetString(buffer, 0, result.Count);
                var outgoing = Encoding.UTF8.GetBytes($"echo:{incoming}");
                await socket.SendAsync(outgoing, WebSocketMessageType.Text, true, context.RequestAborted);
            }
        })
        .WithDisplayName("WebSocketEcho")
        .WithTags("Interfaces");

        return app;
    }

    private sealed class GraphQlRequest
    {
        public string? Query { get; init; }

        public Dictionary<string, object?>? Variables { get; init; }
    }
}
