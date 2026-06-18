# Informe de Mercado — Software de Gestión para Restaurantes (Argentina y LatAm)
### Insumo para PRD de un nuevo SaaS gastronómico con foco en IA conversacional
**Fecha de elaboración:** 17 de junio de 2026 · **Moneda de referencia:** ARS / USD según fuente

> Nota metodológica: todos los datos provienen de fuentes citadas con fecha de consulta. Donde un dato no pudo confirmarse, se marca explícitamente como **"no encontrado / requiere validación"**. No se inventaron precios ni features. Los precios en ARS son altamente volátiles por inflación: tratarlos como referencia del momento de consulta.

---

## 1. Resumen ejecutivo (hallazgos clave)

- **El "gap" de IA conversacional EXISTE en LatAm, pero es estrecho y se está cerrando rápido.** Ningún competidor directo de LatAm (Fudo, Bistrosoft, Maxirest, Loyverse) ofrece hoy un copiloto de analytics conversacional ("preguntale a tu negocio" / text-to-data en lenguaje natural). Pero los referentes globales (Square, Toast) **ya lo lanzaron en oct-2025**. El hueco es geográfico/idiomático, no conceptual.
- **Matiz crítico:** **Maxirest ya comercializa "alertas inteligentes a partir de tus datos", "asesoría automatizada" y big data de precios de la zona.** La pata de **"alertas proactivas"** NO es terreno virgen en Argentina. El diferenciador defendible es la **consulta en lenguaje natural**, no las alertas en sí.
- **La "IA" de Fudo es customer-facing, no analytics.** El "Recepcionista IA" es un bot de WhatsApp para reservas/pedidos de clientes (add-on ~$55.000/mes), no un asistente analítico para el dueño.
- **Facturación electrónica AFIP (hoy ARCA) es una barrera técnica seria y obligatoria.** WSAA (cert X.509), WSFEv1 (CAE/CAEA), tipos de comprobante A/B/C/M, contingencia, multi-CUIT. Todos los competidores ya lo resolvieron → es **tabla de entrada**, no diferenciador.
- **TAM amplio pero con cifras dispares.** FEHGRA: ~67.000 establecimientos gastronómicos; SRT/INDEC: ~26.000 empresas formales de "hoteles y restaurantes" (2023). Orden de magnitud: decenas de miles.
- **Viento de cola fuerte en IA gastronómica (2024-2026):** ~26% de operadores ya usan IA (NRA); 82% de ejecutivos planean aumentar inversión. Riesgo: velocidad de los incumbentes.
- **Macro adverso en Argentina:** caída de consumo en restaurantes ~20% (2024-2025). Presiona márgenes → más demanda de herramientas de ahorro, pero también sensibilidad al precio.

---

## 2. Tabla comparativa de competidores

| Competidor | KDS | POS | FE AFIP | Stock | RRHH | Reservas | Precio (ref.) | Free/trial | IA conversacional (NL) | Alertas proactivas |
|---|---|---|---|---|---|---|---|---|---|---|
| **Fudo** (AR/LatAm) | Sí (add-on) | Sí | Sí (add-on) | Sí | Parcial | Sí (add-on) | ARS: Inicial $20.900 · Avanzado $41.000 · Pro $65.000/mes + módulos | Trial; free no conf. | **No** (su IA es bot WhatsApp p/ clientes) | No confirmado |
| **Maxirest** (AR) | Sí | Sí | Sí (incluido) | Sí (recetas, food cost) | Sí | Sí | Desde $11.996 + IVA/mes | No conf. | **No** (dashboards, no NL) | **Sí — declarado**: "alertas inteligentes", big data de zona |
| **Bistrosoft** (AR/MX/ES) | Sí | Sí | Sí | Sí | No conf. | No conf. | MX ~$799/mes; ES €39/mes; **AR no encontrado** | Sin mínimo | **No** | Parcial |
| **Loyverse** (global) | Sí (free) | Sí (free) | **No nativo AR** | Sí (€25/mes) | Sí (€5/empleado) | — | Core gratis + add-ons | **Sí free real** | **No** | No |
| **Toast** (EEUU, ref.) | Sí | Sí | N/A | Sí | Sí | Sí | N/A AR | — | **Sí — Toast IQ** (oct-2025) | **Sí** |
| **Square** (EEUU, ref.) | Sí | Sí | N/A | Sí | Sí | Sí | N/A AR | Free tier | **Sí — Square AI** (oct-2025) | **Sí** |

> Celdas "no confirmado" requieren validación directa (demo/proveedor). Precios ARS volátiles: revalidar.

---

## 3. El gap de IA — VEREDICTO

**Veredicto: el hueco existe, pero el diferenciador defendible es (a) consulta NL, NO (b) alertas.**

**(a) Consulta en lenguaje natural ("preguntale a tu negocio"):** Ningún competidor LatAm lo ofrece — todos tienen dashboards/reportes (algunos en tiempo real) pero **ninguno** permite escribir *"¿qué plato me dio más margen el mes pasado?"* y recibir respuesta con datos. Maxirest "Mi Maxirest" = analytics visual, no conversacional. Fudo = bot de cara al cliente. **Square AI y Toast IQ ya hacen exactamente esto en EEUU** (ej. *"How did this week's labor costs compare to last?"*) → la feature está probada; el hueco es geográfico/idiomático (LatAm, español, AFIP).

**(b) Alertas proactivas:** El hueco NO es limpio. **Maxirest** ya promete "alertas inteligentes" + "asesoría automatizada"; **BCNRESTO** "alertas automáticas de stock mínimo". Lo que no se encontró es alerta **derivada de IA y contextual** (*"tu food cost subió 4 pts por carnes"*), pero requiere validación en demo.

**Conclusión PRD:**
1. Posicionar el diferenciador en (a) — **copiloto conversacional en español + AFIP nativo** (hueco real y demostrable en LatAm).
2. NO vender "alertas proactivas" como novedad absoluta (Maxirest ya ocupa ese lenguaje). Diferenciar por calidad/IA contextual + combinación con el chat.
3. **Ventana 12-24 meses:** el gap se cierra rápido (Maxirest tiene rol de "Gerente de Analytics, IA & Arquitectura"). El moat = NL conversacional + AFIP nativo + español rioplatense + precio local + datos verticales.

---

## 4. Facturación electrónica AFIP / ARCA — qué resolver

Bajo ARCA (ex AFIP, 2024-2025), los web services SOAP se mantienen. Un POS debe implementar:

1. **WSAA (autenticación):** certificado X.509 de la AC de ARCA; firmar Login Ticket Request → obtener Ticket de Acceso (TA, ~12h). Setup: Administrador de Relaciones, CSR, autorización del servicio.
2. **Autorización de comprobantes:** **WSFEv1** (A/B/C/M sin detalle de ítem — el más usado por POS; CAE/CAEA) o **WSMTXCA** (con detalle). WSFEXV1 (export) y WSCT (turistas) en casos específicos.
3. **CAE:** por comprobante, enviar datos → recibir CAE + vencimiento; almacenar e imprimir (con QR).
4. **Complejidad/riesgos:** gestión de certificados (renovación, multi-CUIT por local), numeración/correlatividad por punto de venta, **contingencia/CAEA** (caídas de ARCA en hora pico = punto sensible), tipos de comprobante según condición IVA, normativa cambiante (mantenimiento continuo).

**Implicancia:** costo de entrada obligatorio, alta complejidad. **Recomendación: evaluar build vs. buy** — hay middlewares argentinos de FE como servicio que abstraen WSAA/WSFEv1 (acelera time-to-market, reduce riesgo regulatorio, a cambio de costo por comprobante). No es diferenciador; es higiene.

---

## 5. TAM y tendencias

- **FEHGRA:** ~67.000 establecimientos gastronómicos (+ ~17.000 hoteleros), dato 2024 (techo).
- **SRT/INDEC:** ~25.900 empresas formales de "hoteles y restaurantes" (feb-2023) — base empleadora.
- **Lectura:** TAM direccionable en Argentina = decenas de miles (~25k formales a ~67k amplio). Cifra exacta restaurantes+bares: **no encontrada / requiere validación**. LatAm amplía sustancialmente (Bistrosoft +25.000 locales en +8 países).
- **Tendencias IA:** ~26% operadores ya usan IA (NRA); 82% ejecutivos aumentarán inversión. Toast survey: 42% probable de adoptar IA para benchmarking, 41% para forecasting. Square AI + Toast IQ (oct-2025). LatAm: alto uso de IA pero **confianza por detrás del uso** → oportunidad de onboarding/educación.
- **Macro AR:** consumo en restaurantes -20% (2024-2025) por menor turismo y dólar → apetito por ahorro pero sensibilidad al precio.

---

## 6. Riesgos e insights para el PRD

**Insights:**
1. **El diferenciador es un bundle, no una feature.** NL conversacional sola es replicable. Moat LatAm = NL en español + AFIP/ARCA nativo + ARS competitivo + verticalización + datos del local.
2. **Reposicionar "alertas".** Diferenciar por IA contextual accionable (explicar *por qué*, sugerir acción) + integración con chat.
3. **AFIP = tabla de entrada.** Resolver bien contingencia/CAEA y multi-CUIT; considerar middleware.
4. **Onboarding y confianza = cuello de botella** (uso alto, confianza baja). El copiloto debe **mostrar sus fuentes/datos** y ser verificable.

**Riesgos:**
- Velocidad de incumbentes (gap cierra en 12-24 meses) → ejecutar rápido, moat de datos/integración.
- Sensibilidad al precio + macro recesivo → validar willingness-to-pay y modelo (¿IA add-on sobre POS base?).
- La IA necesita datos limpios y suficientes → el core (POS+stock+RRHH) captura datos primero; **IA es capa 2**.
- Riesgo de alucinaciones en text-to-SQL → guardrails, validación numérica, trazabilidad.
- **Validaciones pendientes:** precio Bistrosoft AR; alertas reales Fudo/Bistrosoft; AFIP nativo Loyverse AR; TAM exacto; mecanismo de "alertas inteligentes" Maxirest (reglas vs IA).

---

## 7. Fuentes (consulta 17-jun-2026)

**Competidores:** Fudo https://fu.do/es/ · precios https://fu.do/es-ar/precios/ · Recepcionista IA https://blog.fu.do/recepcionista-ia-para-restaurantes-como-tomar-reservas-por-whatsapp-sin-depender-del-telefono · Maxirest https://maxirest.com.ar/ · inteligencia del negocio https://maxirest.com.ar/inteligencia-del-negocio/ · planes https://maxirest.com/planes · rol IA https://theorg.com/org/maxirest/org-chart/leonardo-alvarez · Bistrosoft AR https://bistrosoft.com/ar/software-para-restaurantes/ · MX https://bistrosoft.com/mx/precios/ · Loyverse https://loyverse.com/restaurants-pos · precios https://loyverse.com/pricing · BCNRESTO https://bcnsoft.com.ar/software-para-gastronomicos/

**IA global:** Toast IQ https://pos.toasttab.com/news/toast-launches-toastiq-superpower-future-of-restaurants · RTN Toast (29-oct-2025) https://restauranttechnologynews.com/2025/10/toast-launches-conversational-ai-assistant-to-help-restaurant-operators-work-faster-and-smarter/ · RTN Square (8-oct-2025) https://restauranttechnologynews.com/2025/10/square-goes-all-in-on-restaurants-with-new-ai-voice-ordering-smarter-cost-control-and-integrated-bitcoin-banking/ · Toast survey https://pos.toasttab.com/blog/data/ai-in-restaurants · NRA https://www.restaurantdive.com/news/national-restaurant-assocation-operator-artificial-intelligence-adoption/812418/

**AFIP/ARCA:** WS FE https://www.afip.gob.ar/ws/documentacion/ws-factura-electronica.asp · WSAA https://www.afip.gob.ar/ws/documentacion/wsaa.asp · certificados https://www.afip.gob.ar/ws/documentacion/certificados.asp · manual desarrollador https://www.afip.gob.ar/fe/documentos/manual-desarrollador-ARCA-COMPG-v4-0.pdf · guía 2026 https://developargentina.com/blog/facturacion-electronica-arca-guia-completa-2026

**TAM/tendencias:** FEHGRA https://fehgra.org.ar/acerca-de-fehgra · Infobae SRT https://www.infobae.com/economia/2023/05/17/por-el-impulso-del-turismo-en-el-ultimo-ano-abrieron-mas-de-3300-empresas-del-rubro-de-hoteles-y-restaurantes/ · Ficha CABA https://buenosaires.gob.ar/sites/default/files/2025-02/Ficha%20Gastronom%C3%ADa%20-%20Mayo%202024.pdf · Ámbito consumo https://www.ambito.com/economia/consumo-y-dolar-actividad-restaurantes-cae-20-y-advierten-perdida-turistas-extranjeros-n6082254
