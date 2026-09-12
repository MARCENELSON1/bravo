# La app no estaba lista para la App Store, y el motivo no era técnico

**Proyecto:** BRAVO / Wellnod · **Fecha:** 2026-09-11 · **Rama:** `main`
**Alcance:** paridad web↔mobile, requisitos de la App Store, UX 2026, modo claro/oscuro.
**Commits:** `5028e69`, `534f8f7`, `fddd7f9`

---

## Resumen

Fui a buscar funciones del web que faltaran en el móvil. **Casi no faltaban** —
la paridad ya estaba— pero apareció algo más serio: la app tenía **83 filas de
Ajustes que no hacían nada**, y varias mostraban valores inventados como si
fueran configuración real. Eso es rechazo directo en la revisión de Apple
(guía 2.1, App Completeness) y contradice la premisa del producto: que lo que
se muestra sea cierto.

Además faltaban dos requisitos obligatorios —borrar la cuenta y el manifiesto de
privacidad— y el modo claro tenía tres fallas de contraste medibles.

---

## 1 · Paridad web ↔ móvil

26 rutas en el web contra 29 pantallas en el móvil. Comparadas una por una:

| Encontrado | Estado |
|---|---|
| Drill-down de producto en Finanzas | ❌ faltaba → **construido** |
| Ficha del producto (composición, alertas de insumo) | ❌ falta → no lo hice |
| Invitar personal | ❌ falta → no lo hice |
| Barra (KDS) | ✅ existe, resuelto por rol y no por pantalla |
| Integraciones (AFIP + Mercado Pago) | ✅ existe, adentro de Ajustes |

**Corrección a mi propio análisis:** primero reporté Integraciones como ausente.
No lo está: es una sección real dentro de Ajustes, y mi comparación miraba rutas
en vez de destinos alcanzables.

### Lo que construí

**Drill-down de producto** (`534f8f7`). Tocar un plato en "margen por producto"
abre su detalle: totales del período, evolución del costo por unidad y las
últimas ventas. El backend ya lo calculaba desde `b3b18cd`; faltaba el cliente.

Dos cuidados heredados de esa tanda que había que respetar:

* Los totales y la serie cubren la ventana **entera**; el listado de ventas viene
  **acotado**. El modelo los mantiene separados y la pantalla avisa cuando está
  cortado — si no, un plato muy vendido mostraría de menos sin decirlo.
* La curva se pinta desde `cost_series` (agregada en SQL) y **no** derivándola de
  las líneas, porque eso perdería los días más viejos en silencio.

---

## 2 · Requisitos de la App Store

### 🔴 Lo que bloqueaba, y ya no

**a · Ajustes era decorativa.** 83 filas portadas 1:1 del web; solo 5 tenían una
sección real detrás. Las otras 78 mostraban un botón **"Próximamente"** o —peor—
un valor fabricado: *"Tolerancia de fichaje: 10 min"*, *"Copias: 1"*, *"Zona
horaria: GMT−3"*. Ninguno existía en el backend.

Los botones muertos son rechazo por guía 2.1. Los valores inventados son otra
cosa: alguien los lee y les cree.

La regla que implementé: **una fila se muestra solo si lee estado real o abre una
pantalla que existe**. Y una tab entra solo si tiene contenido — filtrar las
filas sin filtrar las tabs dejaba tabs vacías, que se ven igual de rotas. Las
filas sin backend no se borraron del archivo: quedan como el mapa de lo que falta
y se encienden solas al darles un destino.

De paso quedaron alcanzables dos pantallas que ya existían y no se llegaba a
ellas desde Ajustes: **impresora** y **costos del Asesor**.

**b · No se podía borrar la cuenta.** Requisito 5.1.1(v), obligatorio desde 2022.
Y la fila que lo prometía mostraba "Próximamente" — peor que no tenerla.

Acá hay un filo de diseño: **la cuenta de un dueño ES el local**. El caso de uso
distingue los dos borrados y lo dice *antes*, para que la confirmación no mienta:

* Un empleado se lleva **su acceso**; el local y su historial quedan.
* El último dueño se lleva **el local entero** — cascada de las 44 claves foráneas
  a `tenants`.

Se re-pide la contraseña aunque el token sea válido (un teléfono desbloqueado
sobre la barra no da de baja el negocio de un toque) y, si cae el local, escribir
su nombre. 4 tests fijan los dos caminos.

> Detalle honesto que apareció: con el local borrado, el token de otro empleado
> sigue siendo criptográficamente válido y `/me` responde 404, no 401 — el token
> se valida sin tocar la base. No es un agujero (el filtro por tenant y RLS dejan
> todo vacío), pero el cliente tiene que leerlo como sesión terminada. Queda
> anotado en el test.

**c · Faltaba el manifiesto de privacidad.** Los plugins traían el suyo (por eso
la subida a TestFlight pasaba), pero no el del target de la app, que es el único
que puede declarar qué recolecta. Verificado de punta a punta: `flutter build
ios` lo empaqueta en la raíz del `.app` junto a los 20 de los plugins.

**d · Zonas táctiles chicas.** El botón de quitar un plato medía **26×26pt**
contra los 44 que pide la guía de Apple. Ahora se ve igual y se toca en 44 — es
el control que el mozo aprieta con el pulgar en pleno servicio.

### ✅ Lo que ya estaba bien

Íconos completos (21 tamaños, ninguno faltante), pantalla de carga, declaración
de encriptación, orientaciones para iPhone y iPad, textos de propósito del
Bluetooth, iOS 15 como mínimo.

### ⬜ Lo que te toca a vos (no es código)

Etiquetas de privacidad en App Store Connect —**tienen que coincidir con el
manifiesto** o la revisión lo marca—, capturas, URL de soporte, política de
privacidad, clasificación por edad y la descripción.

---

## 3 · Modo claro y oscuro

No lo miré a ojo: **medí los pares reales** contra el mínimo de WCAG (4,5:1).

**Oscuro: pasan todos.** Texto 17,8:1, atenuado 7,4:1, primario 7,8:1.

**Claro: tres fallas.**

| Par | Antes | Ahora |
|---|---|---|
| Verde de "servido" sobre el fondo | ❌ 2,54:1 | ✅ **5,48:1** |
| Ámbar de "demora" sobre el fondo | ❌ 2,15:1 | ✅ **5,02:1** |
| Texto del botón primario | ⚠️ 3,14:1 | **sin tocar** — ver abajo |

Los dos primeros eran literales `#10B981` y `#E0A800` sueltos en el código en vez
de un token del tema. Ahora hay `successOn` / `warnOn` por tema: **en oscuro el
valor es idéntico al de antes** (cero cambio visual) y en claro se oscurecen
manteniendo el tono.

**El tercero no lo cambié a propósito.** Es blanco sobre el verde de marca
`#00A271`. Pasa para texto grande (mínimo 3,0) y no llega para texto chico.
Cambiarlo es una decisión de marca, no mía — y la paleta del móvil es espejo de
la del web, así que tocarlo de un lado los separaría. **Queda reportado, no
resuelto.**

---

## 4 · UX de 2026

### Lo que ya tenía

Mejor de lo que esperaba: háptica en los flujos operativos (comanda, grilla,
KDS), pull-to-refresh en 18 pantallas, "reducir movimiento" respetado, estados
vacíos en 39 archivos, y Dynamic Type funcionando (nada bloquea el escalado).

### Lo que agregué

**Accesibilidad, que estaba en cero.** La app no tenía un solo `Semantics`: para
VoiceOver, la tarjeta de mesa era una pila de textos sin decir que se toca, y los
tiles de producto no decían precio ni cuántos van cargados. Agregué rótulos donde
más se usa —el rótulo de la mesa junta estado y minutos en una frase, porque
quien escucha no puede saltear con la vista— y etiquetas a los botones de solo
ícono.

**Permiso de notificaciones con explicación previa.** Se pedía **en frío**,
apenas el mozo entraba. iOS pregunta una sola vez: un "No permitir" de reflejo lo
deja sin el aviso de "mesa lista" para siempre, sin forma de volver a pedirlo —
justo la función que hace que la app le sirva en el bolsillo. Ahora va primero
una hoja que explica qué avisos son y qué no; si dice "ahora no", **no se dispara
el diálogo del sistema** y el permiso queda intacto para preguntarle después.

### Lo que anoté y no arreglé

**122 contenedores con alto fijo.** Con el texto del sistema al 200% pueden
cortar contenido. Verificado por inspección, no por prueba: haría falta correr la
app con Dynamic Type al máximo y recorrer las pantallas.

---

## 5 · Lo que NO hice

* **Ficha del producto** (composición de receta, alertas de insumo, evolución) —
  existe en el web y sigue faltando en el móvil.
* **Invitar personal** desde el móvil.
* **El contraste del botón primario** — es decisión de marca y afecta a los dos
  clientes.
* **Probar Dynamic Type al 200%** en las 29 pantallas.
* **Probar VoiceOver de punta a punta.** Agregué los rótulos donde más se usa;
  recorrer la app entera con el lector prendido es otra pasada.

---

## Validación

Backend 855 tests · móvil 66 · `flutter analyze` limpio · `flutter build ios`
verificado tres veces · producción monitoreada en cada deploy (health 200) y el
endpoint nuevo respondiendo.
