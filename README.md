# Lab LLM NetOps

Lab environment untuk demonstrasi integrasi LLM dengan NetBox menggunakan Model Context Protocol (MCP).

## Arsitektur

```mermaid
sequenceDiagram
    participant User
    participant LLM Client
    participant Ollama
    participant NetBox MCP
    participant NetBox

    User->>LLM Client: "list all sites"
    LLM Client->>Ollama: Chat request + tools
    Ollama-->>LLM Client: Tool call: list_sites()
    LLM Client->>NetBox MCP: Execute tool (SSE)
    NetBox MCP->>NetBox: API request
    NetBox-->>NetBox MCP: API response
    NetBox MCP-->>LLM Client: Tool result
    LLM Client->>Ollama: Tool result
    Ollama-->>LLM Client: Final response
    LLM Client-->>User: "Data Center A"
```

## Fitur

- **NetBox MCP Server**: Mengekspos data NetBox via protokol MCP (SSE transport)
- **LLM Client**: Interface chat menggunakan Ollama dengan dukungan tool calling
- **Tools yang tersedia**:
  - `list_sites` - Daftar semua sites
  - `get_device` - Detail device berdasarkan nama
  - `get_ip_address` - Detail IP address
  - `list_ip_addresses` - Daftar semua IP addresses

## Prasyarat

- Docker & Docker Compose
- Ollama server dengan model `llama3.1` (atau model lain yang mendukung tool calling)

## Cara Memulai

1. **Clone dan konfigurasi**
   ```bash
   git clone <repo-url>
   cd lab_llmnetops
   cp netbox/env/netbox.env.example netbox/env/netbox.env
   cp netbox/env/postgres.env.example netbox/env/postgres.env
   cp netbox/env/redis.env.example netbox/env/redis.env
   ```

2. **Edit konfigurasi**
   - Update `docker-compose.yml` dengan alamat Ollama server Anda
   - Sesuaikan env files sesuai kebutuhan

3. **Jalankan services**
   ```bash
   docker compose up -d
   ```

4. **Populate data sample** (opsional)
   ```bash
   python netbox/scripts/populate_netbox.py
   ```

5. **Jalankan LLM Client**
   ```bash
   cd llm-client && ./run_client.sh
   ```

## Struktur Project

```
lab_llmnetops/
├── docker-compose.yml
├── llm-client/           # LLM chat client
│   ├── Dockerfile
│   ├── run_client.sh
│   └── src/client.py
├── netbox/               # Konfigurasi & data NetBox
│   ├── env/              # Environment files
│   ├── data/             # Persistent storage (gitignored)
│   └── scripts/          # Helper scripts
└── netbox-mcp/           # MCP server untuk NetBox
    ├── Dockerfile
    └── src/server.py
```

## Konfigurasi

### Ollama Server
Update `OLLAMA_HOST` di `docker-compose.yml`:
```yaml
environment:
  - OLLAMA_HOST=http://alamat-ollama-anda:11434
  - MODEL_NAME=llama3.1
```

### NetBox Token
Generate token di NetBox Admin panel dan update di `docker-compose.yml`:
```yaml
environment:
  - NETBOX_TOKEN=token-anda-disini
```

## Contoh Penggunaan

```
User: tampilkan semua IP address yang ada di netbox
Assistant: Berikut adalah daftar IP address yang ada di NetBox:
* 10.0.0.1/24 (Gateway Management)
* 172.16.0.10/24 (Web Server)
* 192.168.1.100/24 (Workstation-01)

User: get IP address 172.16.0.10
Assistant: IP 172.16.0.10/24 adalah "Web Server" dengan status Active.
```

## Lisensi

MIT
