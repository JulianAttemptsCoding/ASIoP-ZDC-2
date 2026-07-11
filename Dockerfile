FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
COPY tests ./tests
RUN python -m pip install --no-cache-dir --upgrade pip && \
    python -m pip install --no-cache-dir .
CMD ["python", "-m", "unittest", "discover", "-s", "tests", "-v"]
