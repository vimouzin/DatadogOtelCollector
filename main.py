import logging
from flask import Flask, jsonify
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.instrumentation.flask import FlaskInstrumentor
import os

# Inicializa o aplicativo Flask
app = Flask(__name__)

# Configura os recursos e o provedor de rastreamento do OpenTelemetry
resource = Resource.create({
    "deployment.environment": "prod",
    "service.name": "show-how-to-use-otel-with-datadog",
    "version": "5.2.7"
})

trace.set_tracer_provider(TracerProvider(resource=resource))
tracer = trace.get_tracer(__name__)

otlp_exporter = OTLPSpanExporter(    
    endpoint="https://otel-collector-961033714251.us-east1.run.app:443/v1/traces",
    headers=(("Content-Type", "application/json"),)
)

# Configura um processador de spans e adiciona-o ao provedor de rastreamento
span_processor = BatchSpanProcessor(otlp_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

# Configura o provedor de logs e o exportador
logger_provider = LoggerProvider(resource=resource)
otlp_log_exporter = OTLPLogExporter(
    endpoint="https://otel-collector-961033714251.us-east1.run.app:443/v1/logs",
    headers=(("Content-Type", "application/json"),)
)
log_processor = BatchLogRecordProcessor(otlp_log_exporter)
logger_provider.add_log_record_processor(log_processor)

# Configura o logging do Python para usar o handler do OpenTelemetry
logging_handler = LoggingHandler(logger_provider=logger_provider)
logging_handler.setLevel(logging.INFO)
logging.basicConfig(level=logging.INFO, handlers=[logging_handler])

# Cria uma instância de logger
logger = logging.getLogger(__name__)

# Instrumenta o aplicativo Flask
FlaskInstrumentor().instrument_app(app)

@app.route("/")
def hello_world():
    with tracer.start_as_current_span("hello_world"):
        logger.info("Esta é uma mensagem de log com contexto de rastreamento.")
        return jsonify(message="Hello, World!")

@app.route("/ping")
def ping():
    with tracer.start_as_current_span("ping"):
        return jsonify(message="Pong!")

# Executa o aplicativo Flask
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Default to 5000 if PORT isn't set
    app.run(host='0.0.0.0', port=port)

