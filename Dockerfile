# Use an official Python image
FROM python:3.12.3-slim

# Install Tailscale and dependencies with retry logic for mirror issues
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    git \
    iptables \
    iproute2 \
    nodejs \
    npm \
    || (sleep 5 && apt-get update && apt-get install -y --fix-missing --no-install-recommends curl git iptables iproute2 nodejs npm) && \
    curl -fsSL https://tailscale.com/install.sh | sh && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install uv (Python package manager)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set the working directory
WORKDIR /app

# Copy project files into the container
COPY . .

# Install Python dependencies
RUN pip install -r requirements.txt

# Install Speckit (specify) via uv
RUN uv tool install git+https://github.com/github/spec-kit --force

# Install Claude Code CLI
RUN npm install -g @anthropic-ai/claude-code

# Ensure ~/.local/bin is in PATH for uv tools
ENV PATH="/root/.local/bin:$PATH"

# Copy startup script
COPY cloud_run_entrypoint.sh /app/start.sh
RUN chmod +x /app/start.sh

# Expose the app's port
EXPOSE 8080

# Start services
CMD ["/app/start.sh"]
