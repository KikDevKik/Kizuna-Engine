import logging
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

logger = logging.getLogger(__name__)

class JsonFormatter(logging.Formatter):
    def format(self, record):
        import json
        log_record = {
            "severity": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }
        return json.dumps(log_record)

def setup_telemetry(app):
    provider = TracerProvider()
    try:
        from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
        exporter = CloudTraceSpanExporter()
        provider.add_span_processor(BatchSpanProcessor(exporter))
        logger.info("CloudTrace exporter initialized")
    except Exception as e:
        logger.warning(f"CloudTrace unavailable, using console: {e}")
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    trace.set_tracer_provider(provider)

    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logging.root.addHandler(handler)
    logging.root.setLevel(logging.INFO)
