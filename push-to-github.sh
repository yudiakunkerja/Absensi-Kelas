#!/bin/bash
# ============================================================
# Script Push Otomatis ke GitHub - Absensi Ceria
# Repository: https://github.com/yudiakunkerja/Absensi-Kelas
# ============================================================

set -e

REPO_URL="https://${GITHUB_TOKEN}@github.com/yudiakunkerja/Absensi-Kelas.git"
BRANCH="main"

echo "🎒 Push Otomatis - Absensi Ceria"
echo "================================="

# Pastikan berada di folder absensi-ceria
cd "$(dirname "$0")"

# Inisialisasi git jika belum
if [ ! -d ".git" ]; then
    echo "📁 Inisialisasi git repository..."
    git init
    git branch -M main
fi

# Konfigurasi user git
git config user.email "141396830+YudiGetHub@users.noreply.github.com"
git config user.name "YudiGetHub"

# Set atau update remote
if git remote get-url github-absensi &>/dev/null; then
    git remote set-url github-absensi "$REPO_URL"
    echo "🔗 Remote URL diperbarui"
else
    git remote add github-absensi "$REPO_URL"
    echo "🔗 Remote ditambahkan"
fi

# Buat .gitignore
cat > .gitignore << 'EOF'
# Jangan upload secrets!
.streamlit/secrets.toml
__pycache__/
*.pyc
*.pyo
.env
.DS_Store
EOF

# Stage semua file
git add -A
echo "📝 File yang akan di-push:"
git status --short

# Commit dengan timestamp
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
git commit -m "🎒 Update Absensi Ceria - $TIMESTAMP" 2>/dev/null || echo "ℹ️  Tidak ada perubahan baru, tetap push..."

# Push ke GitHub
echo ""
echo "🚀 Sedang push ke GitHub..."
git push -u github-absensi $BRANCH --force

echo ""
echo "✅ BERHASIL! Kode sudah ada di:"
echo "   https://github.com/yudiakunkerja/Absensi-Kelas"
echo ""
echo "📌 Langkah selanjutnya:"
echo "   1. Buka https://share.streamlit.io"
echo "   2. New app > pilih repo 'Absensi-Kelas'"
echo "   3. Main file: app.py"
echo "   4. Isi Secrets dari file .streamlit/secrets.toml.example"
