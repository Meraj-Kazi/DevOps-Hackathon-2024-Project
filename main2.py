from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import JSONResponse
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import Resource
from sqlalchemy import create_engine, Column, Integer, String, MetaData, Table, DateTime
from databases import Database
import logging_loki
import logging
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# Define SQLAlchemy models
Base = declarative_base()

class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    post_data = Column(String)

# MySQL Database Configuration
DATABASE_URL = "mysql+mysqlconnector://root:password1234@localhost/hackathon"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
metadata = MetaData()

app = FastAPI()

# Configure OpenTelemetry for the second app
trace.set_tracer_provider(TracerProvider(resource=Resource.create({'service.name': 'fastapi-service-2'})))
trace.set_tracer_provider(TracerProvider())
trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(JaegerExporter()))

FastAPIInstrumentor.instrument_app(app)

handler = logging_loki.LokiHandler(
    url="http://localhost:3000/loki/api/v1/push", 
    tags={"application": "my-app"},
    auth=("admin", "password1234"),
    version="1",
)

logger = logging.getLogger("my-logger")
logger.addHandler(handler)
logger.error(
    "Something happened", 
    extra={"tags": {"service": "my-service"}},
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Routes
        
@app.get("/posts")
async def read_post(db: Session = Depends(get_db)):
    post = db.query(Post).all()
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    return post

@app.get("/second")
async def read_second():
    # Simulate some processing
    with trace.get_tracer(__name__).start_as_current_span("second_app_processing"):
        result = [
            {"id": 1234,
             "name": "Jack",
             "post_data": "Jack, Hello from the second app!"
            },
            {"id": 1235,
             "name": "John",
             "post_data": "John, Hello from the second app!"
            },
            ]
        return JSONResponse(content=result)
    