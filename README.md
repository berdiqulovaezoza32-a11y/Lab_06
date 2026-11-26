# BULUTDAGI VIRTUAL TARMOQLAR VA YUKLAMANI BOSHQARISH — laboratoriya (2 akademik soat)

**Muhit:** Windows 10/11, Docker Desktop (Linux containers), Docker Compose. **Python o'rnatish shart emas.** Yuklama generatori ham Docker konteynerida ishlaydi. Avtomatik masshtablash uchun Windows PowerShell (odatiy o'rnatilgan) kerak.

## Topologiya

```text
Windows brauzer: http://127.0.0.1:8080
                  |
  FRONTEND: 172.29.10.0/24
                  |
               NGINX
                  |
  BACKEND: 172.29.20.0/24 (internal)
          /       |       \
        APP-1    APP-2    APP-3 ... APP-4
```

- NGINX `proxy` ikkala tarmoqqa ulangan; `app` faqat izolyatsiyalangan backend tarmog'ida.
- NGINX DNS orqali `app` servisi ko'payganida yangi IP manzillarni ko'radi (`resolver`, `resolve`, NGINX 1.28).
- `loadtest` faqat frontendda; xohlagancha yuklama so'rovlarini yuboradi.
- Lokal port faqat `127.0.0.1:8080` da ochiladi.

## 1. Ishga tushirish

1. Arxivni ZIPdan to'liq chiqaring (masalan, `C:\Lab\Bulut_tarmoqlar_laboratoriyasi_QAYTA`).
2. Docker Desktop dasturini oching va `Engine running` holatini kuting.
3. `START.bat` faylini ikki marta bosing. U ishlamasa shu papkada PowerShell ochib bajaring:

```powershell
docker version
docker compose version
docker compose config
docker compose up -d --build
docker compose ps
```

4. Brauzerda <http://127.0.0.1:8080> ni oching. JSON javob uchun <http://127.0.0.1:8080/api>.

**Muhim:** Birinchi marta Docker `nginx:1.28-alpine` va `python:3.12-alpine` obrazlarini internetdan yuklashi mumkin.

## 2. Virtual tarmoqlar va subnetlar

```powershell
docker network ls
docker network inspect cloud-network-lab_frontend
docker network inspect cloud-network-lab_backend
```

Taqsimot: `frontend` = `172.29.10.0/24`, `backend` = `172.29.20.0/24`. Qaysi konteyner qaysi tarmoqqa ulanganini va IP manzillarni aniqlang.

## 3. Yuklamani muvozanatlash

3 ta ilova nusxasini yarating:

```powershell
docker compose up -d --scale app=3
docker compose ps
```

Bir necha soniyadan so'ng uchala `app`ga so'rov yuborishni tekshiring:

```powershell
1..20 | ForEach-Object { (Invoke-RestMethod http://127.0.0.1:8080/api).instance }
```

Konteyner IDlaridagi farq turli replikalardan kelayotgan javoblarni bildiradi. Qisqa kuzatish davrida barcha replika ko'rinmasligi mumkin; shu sababli pastdagi yuklama testini ham bajaring.

## 4. Yuklama testi (Python o'rnatmasdan)

`YUKLAMA_TESTI.bat` ni ikki marta bosing, yoki:

```powershell
docker compose run --rm --no-deps loadtest --requests 600 --workers 20 --delay-ms 150
```

Natijalar: har bir replika olgan so'rovlar soni, muvaffaqiyatli/xato so'rovlar, throughput (req/s), o'rtacha kechikish (ms) va P95. Ko'p nusxa bilan bir nusxa natijalarini alohida qayd eting.

## 5. Avtomatik masshtablash

1. Bitta `app`ga qayting:

```powershell
docker compose up -d --scale app=1
```

2. **Yangi PowerShell oynasida**, papkada:

```powershell
powershell -ExecutionPolicy Bypass -File .\autoscale.ps1
```

3. **Boshqa PowerShell oynasida**, papkada:

```powershell
docker compose run --rm --no-deps loadtest --requests 3000 --workers 20 --delay-ms 150
```

4. Autoscaler `proxy` access loglarida har 10 soniyada `/api` so'rovlarini sanaydi. Oxirgi davrda >=60 ta bo'lsa bitta replika qo'shadi (max 4); <5 ta so'rov uch davr davomida aniqlansa replikani kamaytiradi (min 1). 20 soniyalik cooldown mavjud. Masshtablashni ko'rish uchun:

```powershell
docker compose ps
```

Agar tez yuklama tugasa, testni qaytaring yoki `--requests 6000` qilib uzaytiring. **Autoscaler** oynasini `Ctrl+C` bilan to'xtating.

> Bu CPU/RAM monitoringiga emas, proxy access loglaridagi so'rovlar soniga asoslangan o'quv autoscaleridir. Docker Compose o'zi avtomatik masshtablashni amalga oshirmaydi.

## 6. Yuqori mavjudlikni ko'rsatish

Autoscaler to'xtaganidan keyin:

```powershell
docker compose up -d --scale app=3
$id = docker compose ps -q app | Select-Object -First 1
docker kill $id
Start-Sleep -Seconds 5
docker compose ps
docker compose run --rm --no-deps loadtest --requests 100 --workers 10 --delay-ms 50
```

`restart: unless-stopped` tufayli `docker kill` qilingan konteyner qayta ishga tushishi mumkin. NGINX boshqa ishlayotgan replikalarga so'rovni yo'naltirishi ham mumkin, lekin qisqa uzilishlar ehtimoli bor. **Bitta kompyuter + bitta Nginx = to'liq HA emas.** HA uchun kamida bir nechta alohida host, redundant balancer va monitoring zarur.

## 7. Natijalarni rasmiylashtirish

| O'lchov | 1 app | 3 app | Autoscale |
|---|---|---|---|
| Replikalar soni | 1 | 3 | 1–4 |
| Muvaffaqiyatli so'rovlar | O'lchang | O'lchang | O'lchang |
| Xatolar | O'lchang | O'lchang | O'lchang |
| Throughput (req/s) | O'lchang | O'lchang | O'lchang |
| O'rtacha javob vaqti (ms) | O'lchang | O'lchang | O'lchang |

Hisobotga `docker network inspect`, `docker compose ps`, yuklama testi va autoscaler konsoli skrinshotlarini qo'shing. Xulosada load balancing, scaling va HA vazifalarini farqlang.

## 8. Yakunlash

`STOP.bat` ni ishga tushiring yoki:

```powershell
docker compose down
```

## Muammolar va yechimlar

- **`no such service: loadtest`**: arxivning aynan shu papkasidagi `compose.yaml` dan foydalanayotganingizni tekshiring: `docker compose config --services` natijasida `proxy`, `app`, `loadtest` chiqishi kerak. PowerShellni shu papkada oching.
- **`port is already allocated`**: port `8080` band. `compose.yaml`dagi `127.0.0.1:8080:80`ni `127.0.0.1:8081:80` qiling, brauzerda 8081ni ishlating.
- **`network overlaps`**: hostdagi mavjud VPN yoki Docker tarmoqlaridan foydalanilayotgan adreslar bilan kesishgan. Compose ichidagi ikkala subnetni bo'sh xususiy diapazonga o'zgartiring.
- **`Cannot connect to the Docker daemon`**: Docker Desktopni yoqing, Linux containers rejimini tekshiring.
- **`502 Bad Gateway`**: `docker compose ps` va `docker compose logs proxy app` bilan tekshiring, `docker compose up -d --build`ni qayta bajaring. Masshtablash vaqtida DNS yangilanishi bir necha soniya davom etishi mumkin.
- **Python topilmaydi**: hech nima o'rnatmang, aynan `docker compose run --rm --no-deps loadtest ...` dan foydalaning.
