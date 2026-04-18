FROM python:3.11-slim

WORKDIR /app

# Install build tools needed by some packages
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .


RUN echo '#!/bin/bash\n\
  if [ -n "$GOOGLE_CREDENTIALS_JSON" ]; then\n\
  echo "$GOOGLE_CREDENTIALS_JSON" > /app/credentials.json\n\
  echo "credentials.json written from secret"\n\
  fi\n\
  exec uvicorn main:app --host 0.0.0.0 --port 7860\n' > /app/start.sh && chmod +x /app/start.sh

EXPOSE 7860

CMD ["/bin/bash", "/app/start.sh"]
