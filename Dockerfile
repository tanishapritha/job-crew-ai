FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# HF Spaces injects secrets as env vars.
# GOOGLE_CREDENTIALS_JSON is the full JSON content of credentials.json.
# At container start, write it to a file so gspread can use it.
RUN echo '#!/bin/bash\n\
if [ -n "$GOOGLE_CREDENTIALS_JSON" ]; then\n\
  echo "$GOOGLE_CREDENTIALS_JSON" > /app/credentials.json\n\
  echo "credentials.json written from secret"\n\
fi\n\
exec uvicorn main:app --host 0.0.0.0 --port 7860\n' > /app/start.sh && chmod +x /app/start.sh

EXPOSE 7860

CMD ["/bin/bash", "/app/start.sh"]
