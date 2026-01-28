# Changelog

Dokumentasi perubahan dan perbaikan pada proyek Lab LLM NetOps.

---

## [2026-01-28] Enhancements: Security, Tools, & Data

### Security & Configuration
- Migrasi konfigurasi sensitif (Token, URL) dari `docker-compose.yml` ke file `.env` terpisah untuk service `netbox-mcp` dan `llm-client`.
- Menambahkan template `.env.example` untuk kemudahan setup.
- Menambahkan file `.env` ke `.gitignore`.

### Features (LLM Client & MCP)
- **New Tool**: Menambahkan `list_devices` di `netbox-mcp` untuk mengambil daftar device lengkap.
- **System Prompt Update**:
  - Menambahkan instruksi **Wajib Bahasa Indonesia**.
  - Menambahkan **Strict Rules** untuk mencegah halusinasi (data fabrication).
  - Mendaftarkan tool `list_devices` ke dalam prompt.

### Data
- Update `netbox/scripts/populate_netbox.py` dengan variasi device yang lebih lengkap (Cisco CSR, Catalyst, ASA; Juniper vSRX, EX4300) dan role baru (Firewall, Distribution Switch).

---

## [2026-01-28] Fix: SSE Connection Timeout pada LLM Client

### Masalah
Error saat menjalankan `run_client.sh`:
```
httpx.RemoteProtocolError: peer closed connection without sending complete message body
Error: Connection closed
```

### Penyebab
SSE connection timeout karena blocking `input()` call. Koneksi SSE di-maintain dalam satu async context, tapi timeout saat menunggu user input.

### Solusi
Refactored `llm-client/src/client.py`:
- Memisahkan fungsi `get_available_tools()` dan `call_mcp_tool()` 
- Fresh SSE connection setiap tool call (reconnect pattern)
- Menggunakan sync loop dengan `asyncio.run()` per operation

### File yang Diubah
- `llm-client/src/client.py` - Refactored connection handling
- `netbox-mcp/src/server.py` - Ditambahkan logging dan `json.dumps()` serialization

### Status
✅ Selesai - LLM Client berhasil memanggil tools NetBox

---

Dokumentasi perubahan dan perbaikan pada proyek Lab LLM NetOps.

---

## [2026-01-28] Fix: API Token Peppers Configuration

### Masalah
Ketika mencoba membuat token di NetBox, muncul error:
```
Unable to save v2 tokens: API_TOKEN_PEPPERS is not defined.
```

### Penyebab
1. **Format environment variable tidak sesuai** - NetBox Docker image tidak membaca `API_TOKEN_PEPPERS` secara langsung, melainkan menggunakan format `API_TOKEN_PEPPER_1`, `API_TOKEN_PEPPER_2`, dst.
2. **Pepper terlalu pendek** - NetBox memerlukan pepper dengan panjang minimal 50 karakter.

### Solusi
Mengubah konfigurasi di `netbox/env/netbox.env`:

**Sebelum:**
```bash
API_TOKEN_PEPPERS=["your-random-pepper-string"]
```

**Sesudah:**
```bash
API_TOKEN_PEPPER_1=Y3ZhyZ2WUyq7rNPgnoRPxSWdG3LzNV9JI06fEXem5DvZGsT5MU0NY3Bip6U8
```

### Langkah Perbaikan
1. Generate pepper string dengan minimal 50 karakter menggunakan:
   ```bash
   openssl rand -base64 60 | tr -d '/+=\n' | head -c 60
   ```
2. Update `netbox/env/netbox.env` dengan format yang benar
3. Recreate containers:
   ```bash
   docker compose up -d --force-recreate netbox netbox-worker netbox-housekeeping
   ```

### File yang Diubah
- `netbox/env/netbox.env` - Perbaikan format API_TOKEN_PEPPER_1

### Status
✅ Selesai - Token creation berfungsi normal

---
