import os

# Avoid LangSmith noise in unit tests unless explicitly enabled.
os.environ.setdefault("LANGCHAIN_TRACING_V2", "false")
