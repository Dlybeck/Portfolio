# Use an official Python image
FROM python:3.12.3-slim

# Install Tailscale and dependencies with retry logic for mirror issues
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    iptables \
    iproute2 \
    || (sleep 5 && apt-get update && apt-get install -y --fix-missing --no-install-recommends curl iptables iproute2) && \
    curl -fsSL https://tailscale.com/install.sh | sh && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy project files into the container
COPY . .

# Install Python dependencies
RUN pip install -r requirements.txt

# Copy startup script
COPY cloud_run_entrypoint.sh /app/start.sh
RUN chmod +x /app/start.sh

# Expose the app's port
EXPOSE 8080

# Start services
CMD ["/app/start.sh"]
