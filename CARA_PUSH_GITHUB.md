# 🚀 Cara Push ke GitHub — Absensi Ceria

## Cara Termudah: Copy-Paste ke Shell Replit

Buka **Shell** di Replit (tab "Shell" di bawah), lalu copy-paste perintah ini sekaligus:

```bash
cd /home/runner/workspace/absensi-ceria && \
git init && \
git config user.email "141396830+YudiGetHub@users.noreply.github.com" && \
git config user.name "YudiGetHub" && \
git remote add origin https://${GITHUB_TOKEN}@github.com/yudiakunkerja/Absensi-Kelas.git && \
git add -A && \
git commit -m "🎒 Absensi Ceria - Initial commit" && \
git branch -M main && \
git push -u origin main --force && \
echo "✅ SUKSES! Cek: https://github.com/yudiakunkerja/Absensi-Kelas"
```

Selesai! Kode kamu sudah ada di GitHub.

---

## Untuk Update Berikutnya (setelah ada perubahan)

Setiap kali ada perubahan, jalankan ini di Shell:

```bash
cd /home/runner/workspace/absensi-ceria && \
git add -A && \
git commit -m "🔄 Update $(date '+%Y-%m-%d %H:%M')" && \
git push origin main && \
echo "✅ Update berhasil!"
```

---

## Tidak Perlu Khawatir Tentang Token

Token GITHUB_TOKEN sudah tersimpan aman di Replit Secrets dan langsung terbaca otomatis oleh perintah `${GITHUB_TOKEN}` di atas.
