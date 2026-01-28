# Changelog

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
