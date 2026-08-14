FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml README.md LICENSE ./
COPY contextbench ./contextbench
COPY cases ./cases
COPY examples ./examples

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

EXPOSE 8765

CMD ["sh", "-c", "python3 -m contextbench.cli --demo && python3 -m http.server 8765 --bind 0.0.0.0 --directory results"]
