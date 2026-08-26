# Cloudflare edge-geo — Fase C de la landing internacional

Rutea la landing por país en el edge: **AR → `/` (es/ARS)**, **resto → `/en/` (en/USD)**,
sin romper SEO. El build ya genera las dos variantes (`dist/index.html` + `dist/en/index.html`
con hreflang); este Worker solo decide a cuál mandar al **humano**.

## Requisito previo (infra tuya)

Migrar el DNS de `wellnod.com` a **Cloudflare** (hoy Namecheap → Railway):

1. Crear el sitio `wellnod.com` en Cloudflare (plan Free alcanza).
2. Cloudflare te da 2 nameservers → cargarlos en Namecheap (Custom DNS).
3. En Cloudflare, recrear los registros que hoy apuntan a Railway:
   - `wellnod.com` y `www` → CNAME al dominio de Railway del service `landing` (proxy **naranja** ON).
   - `app` y `api` → sus CNAME a Railway (pueden quedar proxy **gris**/DNS-only si preferís no tocar cookies; ver [[deploy-railway]]).
4. Esperar propagación (Cloudflare avisa cuando está activo).

> Como `app.` y `api.` son same-site con `wellnod.com`, no cambia el esquema de cookies
> (sigue `COOKIE_SAMESITE=lax`). El proxy naranja solo hace falta en `wellnod.com`/`www`
> (los que pasan por el Worker).

## Deploy del Worker

Con [wrangler](https://developers.cloudflare.com/workers/wrangler/):

```bash
cd landing/cloudflare
npx wrangler deploy geo-worker.js --name wellnod-geo
```

Luego, en el dashboard de Cloudflare → **Workers Routes**, asociar el Worker a:

- `wellnod.com/` (la raíz)

Con eso alcanza: el Worker solo actúa en `/`; `/en/`, assets, sitemap, etc. pasan directo.
(Si preferís cubrir todo, la ruta `wellnod.com/*` también funciona — el Worker deja pasar
todo lo que no sea `/`.)

## Verificación (Fase D)

- IP AR (o `curl -H "CF-IPCountry: AR"` desde el edge) → `wellnod.com/` = **ES/ARS**.
- IP US (VPN) sin cookie → **302** a `/en/` = **EN/USD**.
- `wellnod.com/en/` directo → EN/USD (simula bot/link, sin redirect).
- Google Search Console → hreflang sin errores, las dos indexadas.
- Lighthouse SEO OK en las dos, sin flash de idioma.

## Cómo funciona (SEO-safe)

- **Nunca** redirige por User-Agent → los bots crawlean `/` y `/en/` directo.
- Solo el **humano** en `/` con país ≠ AR y sin cookie recibe un `302` a `/en/`.
- La cookie `wellnod_region=ar|intl` (selector del footer, pendiente en la UI) es un
  override explícito; el Worker solo la lee.
