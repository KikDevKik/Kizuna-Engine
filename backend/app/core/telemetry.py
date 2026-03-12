import json
import logging
import os
from datetime import datetime
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

def setup_telemetry(app):
    # Initialize TracerProvider
    provider = TracerProvider()

    # Configure exporter based on environment
    if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
        exporter = CloudTraceSpanExporter()
    else:
        exporter = ConsoleSpanExporter()

    processor = BatchSpanProcessor(exporter)
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)

    # Instrument FastAPI automatically
    FastAPIInstrumentor.instrument_app(app)

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage()
        }

        # Check if the message is already a JSON string (for our custom metrics)
        try:
            if isinstance(record.msg, str) and record.msg.strip().startswith("{"):
                parsed_msg = json.loads(record.msg)
                log_record.update(parsed_msg)
                # Keep the original string message as a fallback or if it's partly structured
                log_record["message"] = "Structured Event"
        except Exception:
            pass # Keep it as a normal message

        # Include any extra attributes added to the log record
        if hasattr(record, 'extra_data') and isinstance(record.extra_data, dict):
            log_record.update(record.extra_data)

        # Include exception traceback if available
        if record.exc_info:
            log_record["exc_info"] = self.formatException(record.exc_info)

        return json.dumps(log_record)

def configure_json_logging():
    # Remove all handlers from the root logger
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Set up a new console handler with our JSON formatter
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(JsonFormatter())
    root_logger.addHandler(console_handler)
    # Default level can be overridden elsewhere
