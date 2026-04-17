var builder = WebApplication.CreateBuilder(args);

// Basic services
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

var app = builder.Build();

// Swagger in development
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

// Minimal health endpoint
app.MapGet("/", () => Results.Ok(new
{
    service = "Aether.API",
    status = "running",
    timestamp = DateTimeOffset.UtcNow
}));

app.MapGet("/health", () => Results.Ok(new
{
    status = "healthy",
    service = "Aether.API",
    utc = DateTimeOffset.UtcNow
}));

app.Run();