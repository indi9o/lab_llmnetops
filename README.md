# Lab LLM NetOps

A lab environment demonstrating LLM integration with NetBox using Model Context Protocol (MCP).

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   LLM Client    │────▶│  NetBox MCP     │────▶│    NetBox       │
│   (Ollama)      │ SSE │    Server       │ API │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## Features

- **NetBox MCP Server**: Exposes NetBox data via MCP protocol (SSE transport)
- **LLM Client**: Chat interface powered by Ollama with tool calling
- **Available Tools**:
  - `list_sites` - List all sites
  - `get_device` - Get device details by name
  - `get_ip_address` - Get IP address details
  - `list_ip_addresses` - List all IP addresses

## Prerequisites

- Docker & Docker Compose
- Ollama server with `llama3.1` model (or compatible model with tool calling support)

## Quick Start

1. **Clone and configure**
   ```bash
   git clone <repo-url>
   cd lab_llmnetops
   cp netbox/env/netbox.env.example netbox/env/netbox.env
   cp netbox/env/postgres.env.example netbox/env/postgres.env
   cp netbox/env/redis.env.example netbox/env/redis.env
   ```

2. **Edit configuration**
   - Update `docker-compose.yml` with your Ollama server address
   - Modify env files as needed

3. **Start services**
   ```bash
   docker compose up -d
   ```

4. **Populate sample data** (optional)
   ```bash
   python netbox/scripts/populate_netbox.py
   ```

5. **Run LLM Client**
   ```bash
   cd llm-client && ./run_client.sh
   ```

## Project Structure

```
lab_llmnetops/
├── docker-compose.yml
├── llm-client/           # LLM chat client
│   ├── Dockerfile
│   ├── run_client.sh
│   └── src/client.py
├── netbox/               # NetBox configuration & data
│   ├── env/              # Environment files
│   ├── data/             # Persistent storage (gitignored)
│   └── scripts/          # Helper scripts
└── netbox-mcp/           # MCP server for NetBox
    ├── Dockerfile
    └── src/server.py
```

## Configuration

### Ollama Server
Update `OLLAMA_HOST` in `docker-compose.yml`:
```yaml
environment:
  - OLLAMA_HOST=http://your-ollama-server:11434
  - MODEL_NAME=llama3.1
```

### NetBox Token
Generate a token in NetBox Admin panel and update in `docker-compose.yml`:
```yaml
environment:
  - NETBOX_TOKEN=your-token-here
```

## Example Usage

```
User: list all sites in netbox
Assistant: Here are the sites in NetBox:
- Data Center A

User: get IP address 172.16.0.10
Assistant: IP 172.16.0.10/24 is assigned to "Web Server" with status Active.
```

## License

MIT
