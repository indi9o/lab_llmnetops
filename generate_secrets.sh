#!/bin/bash
# Script untuk generate semua secret keys untuk NetBox
# Jalankan: ./generate_secrets.sh

echo "=== NetBox Secret Keys Generator ==="
echo ""
echo "SECRET_KEY=$(openssl rand -base64 50 | tr -d '/+=\n' | head -c 50)"
echo "FIELD_ENCRYPTION_KEY=$(openssl rand -hex 32)"
echo "API_TOKEN_PEPPER_1=$(openssl rand -base64 60 | tr -d '/+=\n' | head -c 60)"
echo ""
echo "Copy nilai di atas ke file netbox/env/netbox.env"
