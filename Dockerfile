# Use Python 3.12
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install poetry
RUN pip install poetry

# Copy poetry files
COPY pyproject.toml poetry.lock ./

# Copy necessary folders and files
COPY client /app/client
COPY utils /app/utils
COPY server /app/server
COPY agent /app/agent

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

# Expose port 8888
EXPOSE 8888

# Set the entrypoint
ENTRYPOINT ["sh", "-c", "poetry run python -m server.server"]