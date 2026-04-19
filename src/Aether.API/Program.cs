using Aether.API.Endpoints;

var builder = WebApplication.CreateBuilder(args);

// Basic services
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

var app = builder.Build();

app.UseWebSockets();

// Swagger in development
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

// Root endpoint
app.MapGet("/", () => Results.Ok(new
{
    service = "Aether.API",
    status = "running",
    timestamp = DateTimeOffset.UtcNow
}));

// Health endpoint
app.MapGet("/health", () => Results.Ok(new
{
    status = "healthy",
    service = "Aether.API",
    utc = DateTimeOffset.UtcNow
}));

// Domain endpoints
app.MapIntelligenceEndpoints();
app.MapIncidentCommandEndpoints();
app.MapConnectorEndpoints();
app.MapUseCasesEndpoints();
app.MapInterfaceEndpoints();

app.Run();