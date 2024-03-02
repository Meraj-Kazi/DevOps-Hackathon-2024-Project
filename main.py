from fastapi import FastAPI
from fastapi.responses import JSONResponse
import httpx
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.export import ConsoleSpanExporter

app = FastAPI()

# Configure OpenTelemetry
trace.set_tracer_provider(TracerProvider(resource=Resource.create({'service.name': 'fastapi-service'})))
trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(JaegerExporter()))

# Instrument FastAPI and HTTPX
FastAPIInstrumentor.instrument_app(app)
HTTPXClientInstrumentor().instrument()

# Sample FastAPI route
@app.get("/")
async def read_root():
    return {"Hello": "World"}

# New API endpoint
@app.get("/items/{item_id}")
async def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}

# New API endpoint
@app.get("/abc")
async def read_item():
    x = 25
    y = 30
    z = x + y * 2 - 455
    return {"Score": z}

@app.get("/call-second")
async def read_root():
    with trace.get_tracer(__name__).start_as_current_span("first_app_processing"):
        # Make an HTTP request to the second app
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8001/second")

        # Extract information from the response
        result = response.json()
        return JSONResponse(content=result)
    
@app.get("/get-twitter-posts")
async def read_root():
    with trace.get_tracer(__name__).start_as_current_span("first_app_processing"):
        # Make an HTTP request to the second app
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8001/posts")

        # Extract information from the response
        result = response.json()
        return JSONResponse(content=result)