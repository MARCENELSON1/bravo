# El circuito de cobro que nadie auditó

**Proyecto:** BRAVO · **Fecha:** 2026-09-05 · **Rama:** `main` · **Commit base:** `824a04e`
**Alcance:** el circuito de cobro por QR — 3.122 líneas nuevas, sin auditoría previa.
**Modo:** solo lectura — no se modificó ningún archivo.

Qué calcula hoy el backend cuando un comensal pide y paga desde el QR de la mesa, leído como asientos y no como código.

---

> ## ⚠️ Estado al 2026-09-10 — leer antes de trabajar sobre este documento
>
> Cada hallazgo se verificó contra el código después de escribirse esta auditoría.
> **Cinco eran reales y están arreglados** (`bac3c54`, `639ced1`). **Tres no lo
> eran** — están marcados abajo con ❌ y **no hay que trabajarlos**.
>
> | Ref. | Verificación | Estado |
> |---|---|---|
> | H1 | Confirmado | ✅ Arreglado |
> | H2 | Confirmado | ✅ Arreglado |
> | H3 | ❌ **Falso** | No se toca |
> | H4 | Confirmado | ✅ Arreglado |
> | H5 | Confirmado | ✅ Cae con H1 |
> | H6 | ⚠️ **Al revés** | Desaparece con H1 |
> | H7 | ❌ **Falso** | No se toca |
> | H8 | Confirmado (sobredimensionado) | ✅ Arreglado |
> | H9 | Confirmado | ✅ Arreglado |
>
> **Contexto que falta en el informe y cambia la urgencia:** al momento de
> escribirse, el canal auditado estaba **apagado** — 0 de 8 locales con prepago
> habilitado y una sola orden prepaga en la historia, cancelada. No se apagó un
> incendio: se sacó una mina antes de pisarla.
>
> **Lección de método:** los dos falsos positivos salen de la misma falta —
> auditar el circuito de cobro sin mirar el módulo de caja (H7) y asignar
> severidad sin medir el alcance en los datos (H1 encabezando la lista siendo
> código apagado).

---

## 0. Por qué esto quedó afuera

Existe una auditoría de fórmulas financieras hecha sobre el commit `19c1ced` (`docs/audits/2026-08-28-auditoria-formulas-financieras.md`): 23 hallazgos sobre ratios, costeo de recetas y KPIs. Sigue siendo válida en lo suyo — verifiqué que los archivos de KPIs y costeo no se tocaron desde entonces.

Pero entre ese commit y hoy entraron 123 commits que agregaron un circuito de plata entero: **carta QR, autopedido, modificadores de plato, cuenta de mesa, división de cuenta y autoservicio con pago anticipado**. Nada de eso pasó por auditoría. Es, además, la parte del sistema donde el comensal mueve dinero *sin que haya un cajero mirando*.

---

## 1. El marco: acá conviven dos libros

Todo lo que sigue se entiende mejor sabiendo que el sistema lleva dos registros paralelos que *deberían* reconciliar y no siempre lo hacen. Es la distinción clásica entre lo devengado y lo percibido, sólo que acá está implementada en dos tablas distintas que se escriben en momentos distintos.

### Libro 1 · Devengado — Ventas

Cuando una comanda se da por saldada, el sistema escribe un registro de venta: importe, importe neto de IVA, costo de la mercadería vendida y categoría de cada plato. Ese registro es la **única** fuente de todo el tablero de gestión.

De acá salen: food cost %, costo de personal %, prime cost, margen bruto, margen neto, punto de equilibrio, ticket promedio, RevPASH, rotación de inventario y las proyecciones a fin de mes.

> tabla `sale_facts` · se escribe en `backend/app/application/analytics/projection.py:62`

### Libro 2 · Percibido — Cobros

Cada movimiento de dinero real: método, importe, propina, comisión de la pasarela, importe neto, caja a la que se imputa y estado (pendiente / confirmado / fallido / devuelto).

De acá salen: el arqueo Z, el neto del panel de inicio y la conciliación con Mercado Pago.

> tabla `payments` · se escribe en `backend/app/application/payment/use_cases.py:204`

**La regla que el sistema se puso a sí mismo:** el Libro 1 sólo se escribe cuando la comanda llega al estado `PAID`. Todos los hallazgos críticos que siguen son variantes del mismo problema: *casos donde entra plata pero la comanda nunca llega a* `PAID`.

---

## 2. Resumen de hallazgos

Ordenado por impacto sobre los estados, no por dificultad de arreglo.

| Ref. | Severidad | Hallazgo | Cuenta afectada |
|---|---|---|---|
| H1 | 🔴 Crítica | La venta del autoservicio prepago nunca se registra, pero el stock sí se descarga | Ventas · CMV · Existencias |
| H2 | 🔴 Crítica | El saldo de la mesa ignora los cobros en curso: se puede cobrar dos veces lo mismo | Caja · Pasivo por devolver |
| H3 | 🟠 Alta | Una devolución no vuelve a abrir el saldo de la mesa | Deudores por venta |
| H4 | 🟠 Alta | La comisión estimada y la real se calculan sobre bases distintas | Gastos bancarios |
| H5 | 🟠 Alta | Sin una acción manual del salón, la venta prepaga queda fuera de los libros para siempre | Ventas |
| H6 | 🟡 Media | Camino posible de doble registración de la misma venta | Ventas · Existencias |
| H7 | 🟡 Media | Las propinas cobradas no tienen cuenta de pasivo | Propinas a liquidar |
| H8 | 🟡 Media | Los adicionales del plato se funden en el precio unitario | Análisis de rentabilidad |
| H9 | 🟡 Media | Se usan decimales de punto flotante en la frontera con Mercado Pago | Conciliación |

---

## 3. Los hallazgos, uno por uno

### H1 — 🔴 La venta del autoservicio prepago nunca llega al libro de ventas

**Qué pasa en el salón.** Un comensal escanea el QR, arma su pedido y paga *antes* de comer. Mercado Pago confirma. La comanda se manda a cocina. Todo funciona, el dinero está en la cuenta.

**Qué pasa en los libros.** El sistema decide, a propósito, *no* marcar esa comanda como pagada — porque marcarla liberaría la mesa mientras la gente todavía está comiendo. Razonable desde la operación. Pero la escritura del libro de ventas está condicionada a ese mismo estado. Resultado: se descuenta la mercadería del inventario y no se registra ni la venta ni el costo de esa venta.

| Lo que debería asentarse | Lo que el sistema asienta hoy |
|---|---|
| Caja / Banco — **debe** | Caja / Banco — **debe** |
| Ventas — **haber** | Ventas — ❌ *no se escribe* |
| CMV — **debe** | CMV — ❌ *no se escribe* |
| Mercaderías — **haber** | Mercaderías — **haber** |

**Cadena de evidencia**

1. El webhook de Mercado Pago confirma el pago y deriva la comanda prepaga a una rutina especial — `backend/app/application/payment/use_cases.py:407`.
2. Esa rutina declara explícitamente en su comentario que *no* marca la comanda como pagada — `backend/app/application/payment/use_cases.py:434`.
3. Acto seguido dispara los efectos de venta, entre ellos la escritura del libro de ventas.
4. Pero esa escritura arranca comprobando el estado y corta si la comanda no está pagada — `backend/app/application/analytics/projection.py:67`. Sale sin escribir nada.
5. El descuento de stock, en cambio, **no** tiene esa comprobación — `backend/app/application/inventory/consume.py:48`. Se ejecuta igual.

**Impacto.** Todo el canal QR con pago anticipado es invisible para Analíticas, Finanzas y el Asesor. Los ingresos quedan subvaluados; el inventario se vacía sin contrapartida. El food cost % y el margen se calculan sobre una base que ignora ese canal, y la caja muestra plata que las ventas no explican. Cuanto más se use el autoservicio, más grande el descuadre.

**Cambio propuesto.** Separar dos conceptos que hoy están pegados: *la mesa está ocupada* y *la venta está registrada*. Que la escritura del libro de ventas dependa de que el cobro esté confirmado y cubra el total, no del estado de la comanda. La comanda puede seguir viva en el plano del salón sin bloquear la registración.

---

### H2 — 🔴 Dos comensales dividiendo la cuenta pueden pagarla entera cada uno

**Cómo se calcula el saldo hoy.** Saldo = total de las comandas abiertas de la mesa − cobros *confirmados*. Un cobro que está en curso (el comensal abrió el checkout de Mercado Pago y todavía no terminó de pagar) no reserva nada.

**La consecuencia.** Dos personas abren la app al mismo tiempo para dividir la cuenta. Las dos ven el saldo completo. Las dos pueden iniciar un cobro por el total. El límite «el importe no puede superar el saldo» se valida cuando se **crea** el cobro, no cuando se **confirma**. Los dos cobros se confirman y el local cobra el doble.

**Y encima queda oculto.** El saldo se muestra con un piso en cero. Un excedente de $12.000 no se ve como saldo negativo: se ve como saldo cero, igual que una mesa correctamente saldada.

| Consumo por $20.000, dos pagos | Lo que muestra el sistema |
|---|---|
| Total de la mesa — 20.000 | Total — 20.000 |
| Cobro A confirmado — 20.000 | Pagado — 40.000 |
| Cobro B confirmado — 20.000 | Saldo real — ❌ −20.000 |
| **Ingresado — 40.000** | Saldo mostrado — ❌ 0 |

**Cadena de evidencia**

1. El cálculo del saldo suma únicamente cobros entrantes en estado confirmado — `backend/app/application/order/table_bill.py:119-124`.
2. La rutina que elige qué comanda cobrar aplica el mismo criterio — `backend/app/application/payment/pay_table_bill.py:157-172`.
3. El tope `importe ≤ saldo` se verifica al crear el cobro — `backend/app/application/payment/pay_table_bill.py:124-128` — y nunca se vuelve a verificar cuando el webhook lo confirma.
4. El saldo se publica con piso en cero — `backend/app/application/order/table_bill.py:131`.

**Impacto.** Cobros en exceso que nadie ve. No existe cuenta de pasivo por devolver, ni alerta, ni traza. El comensal reclama por fuera del sistema y el local no tiene con qué contrastar. El riesgo crece justo en el escenario que la función existe para resolver: mesas grandes dividiendo la cuenta.

**Cambio propuesto.** Tres cosas, en orden. Primero: que los cobros en curso descuenten saldo disponible — quien inicia un pago reserva su parte por unos minutos. Segundo: revalidar el tope contra el saldo *al confirmar*, no sólo al iniciar. Tercero: dejar de esconder el excedente — si sobra plata, que se muestre como saldo a favor del comensal y quede registrado como pasivo.

---

### H3 — ❌ FALSO · Una devolución no vuelve a abrir el saldo

> **No se arregla: el problema no existe.** Un reembolso NO crea un movimiento
> saliente — cambia el estado del cobro original a `REFUNDED`. El cálculo del
> saldo exige `CONFIRMED`, así que ese cobro deja de contar solo y el saldo se
> reabre sin restar nada. En prod: **77 egresos, 0 con comanda asociada** — no
> existen salidas sobre una orden que netear. Cubierto por
> `test_un_reembolso_deja_de_contar_solo`.

El saldo suma únicamente movimientos *entrantes*. Los salientes — devoluciones, contracargos, anulaciones — no se restan de lo ya pagado. Si se le devuelve la plata a un comensal, la mesa sigue figurando como saldada.

En términos contables: se cancela el crédito con una registración que el cálculo del saldo no lee. El deudor por venta vuelve a existir en la realidad pero no en la pantalla.

**Cambio propuesto.** Que el saldo se calcule sobre el neto del movimiento — entradas menos salidas — en lugar de sólo entradas. Es el mismo criterio que ya aplica el arqueo de caja para los movimientos manuales de caja, así que hay precedente interno.

---

### H4 — 🟠 La comisión estimada y la real no miden lo mismo

**El fondo del asunto: la propina no es plata del local, pero el costo de cobrarla sí lo paga el local.**

Cuando el comensal paga $10.000 de comida + $1.000 de propina, por la cuenta del local pasan $11.000. Pero sólo $10.000 son suyos. Los otros $1.000 son del mozo — el local los cobra *por cuenta y orden de un tercero*. Mercado Pago no hace esa distinción: le cobra comisión a los $11.000 completos.

**El número, paso a paso** — venta $10.000 · propina $1.000 · tasa configurada 3,5%:

| Momento | Qué calcula el sistema | Resultado |
|---|---|---|
| Al registrar el cobro | 3,5% sobre **$10.000** (sólo la venta) | comisión $350 → neto $9.650 |
| Lo que hace MP | 3,5% sobre **$11.000** (venta + propina) | comisión $385 → deposita $10.615 |
| Al confirmar el webhook | pisa la estimada: neto = $10.000 − $385 | comisión $385 → neto $9.615 |

El local recibe $10.615, le da $1.000 al mozo, se queda con $9.615. **El neto final está bien** — no hay error aritmético. Lo que hay son tres cosas distintas:

**1 · La estimación miente, siempre para el mismo lado.** $35 de diferencia. No es aleatorio: es exactamente *tasa × propina*. Aparece en cada cobro con propina, siempre subestimando el costo. Peor: **la tasa viene en cero por defecto** — si el dueño nunca la configuró, la estimación dice comisión $0 hasta que llega el webhook.

**2 · El campo comisión dejó de ser coherente con el campo venta.** Después del webhook conviven en el mismo registro `venta = $10.000` y `comisión = $385`. Quien quiera controlar *«¿me están cobrando la tasa pactada?»* divide y obtiene **3,85%**, no 3,5%. La comisión guardada corresponde a una base que no está guardada en ninguna parte: no hay forma de auditar la tasa desde los datos del sistema.

**3 · Nadie decidió que el local pague esto.** Que el local absorba la comisión sobre la propina del mozo es una **decisión de negocio**, y es defendible — muchos locales la toman a propósito, para que el mozo cobre la propina íntegra. Pero nadie la tomó. Es una consecuencia emergente de dos decisiones técnicas escritas en momentos distintos: el adaptador de MP manda la propina como segundo ítem del mismo cobro, y el cálculo de la comisión usa sólo el importe de la venta. Ninguna de las dos es incorrecta por separado. Juntas, le transfieren un costo al local que nadie cuantificó. En un local con 15% de propina promedio y 4% de comisión, es **0,6% de la facturación**.

| Cálculo | Fórmula | Dónde |
|---|---|---|
| Comisión estimada | `redondeo(venta × tasa / 10000)` | `payment/use_cases.py:201` |
| Comisión real | `neto = venta − comisión_real(venta + propina)` | `payment/use_cases.py:401-403` |

**Cambio propuesto.** Estimar la comisión sobre venta + propina, para que la estimación y el cierre midan lo mismo. Y separar en el registro del cobro la comisión atribuible a la venta de la atribuible a la propina, para que la decisión de quién la absorbe sea visible y configurable.

---

### H5 — 🟠 Sin «liberar mesa», la venta prepaga queda fuera de los libros para siempre

Complemento operativo de H1. La comanda prepaga sólo llega al estado pagado cuando alguien del salón aprieta *Liberar mesa*. Si nadie lo hace — cierre de turno apurado, el mozo se olvida, el comensal se va temprano — la comanda queda en un limbo permanente.

Ni siquiera la queda a salvo la herramienta de reconstrucción del libro de ventas, porque ésta recorre sólo las comandas ya pagadas.

Hay un agravante silencioso: esa acción manual marca la comanda como pagada **pero tampoco dispara la escritura del libro de ventas** — `backend/app/application/order/use_cases.py:924-930`. Así que ni apretando el botón se corrige H1 por sí solo.

**Cambio propuesto.** Cae solo si se resuelve H1: desacoplada la registración del estado de la comanda, «liberar mesa» pasa a ser una acción puramente operativa sin consecuencia contable. Mientras tanto, correr la reconstrucción del libro de ventas como control periódico y contrastar contra la caja.

---

### H6 — ⚠️ AL REVÉS · Existe un camino de doble registración de la misma venta

> **Está descrito como riesgo y era lo contrario.** En una comanda prepaga ese
> segundo cobro la marcaba PAID y **recién ahí se registraba la venta** — porque
> por H1 nunca se había registrado. No duplicaba: era la única vía de
> recuperación. Desapareció al arreglar H1, que era la conclusión correcta.

Si sobre una comanda prepaga se registra después otro cobro — un adicional, un ajuste del cajero — la rutina normal ve que lo cobrado ya cubre el total y que la comanda todavía no figura pagada. Entonces la marca pagada y dispara los efectos de venta *por segunda vez*.

En la práctica no duplica, porque tanto la escritura del libro de ventas como el descuento de stock chequean antes si ya existe un registro para esa comanda. Pero la corrección depende enteramente de esos dos chequeos: el diseño permite el doble disparo y confía en que la capa de abajo lo absorba.

**Cambio propuesto.** No es urgente. Al resolver H1 con un único punto de registración, este camino desaparece por construcción. Conviene dejar un test que fije el comportamiento antes de tocarlo.

---

### H7 — ❌ FALSO · Las propinas no tienen cuenta de pasivo

> **No se arregla: el circuito ya existe completo.** `app/application/cashier/`
> tiene reporte por mozo con `earned` / `paid` / `pending`, el total pendiente de
> liquidar, y `POST /cashier/tips/payout` con su registro. El informe propone
> construir las tres cosas que ya están: no se revisó ese módulo.

El tratamiento actual es correcto en lo esencial: la propina viaja sobre el importe de la venta, no cancela deuda de la comanda y no entra al libro de ventas. Bien — no es ingreso del local.

Lo que falta es la contrapartida. El local *cobra* la propina y después *la debe*. Hoy ese dinero entra a la caja y aparece en el arqueo Z mezclado con las ventas, sin una cuenta que diga cuánto hay pendiente de liquidar al personal ni un registro de cuándo se liquidó.

**Cambio propuesto.** Una cuenta de propinas a liquidar, con su circuito de liquidación al personal. El dato ya está guardado por cobro; lo que falta es acumularlo, mostrarlo y darle salida.

---

### H8 — 🟡 Los adicionales se funden en el precio unitario del plato

Cuando el comensal elige adicionales (agregar panceta, doble queso), el sistema suma esos importes al precio unitario de la línea: *una* milanesa a $8.000 con panceta de $1.200 se registra como una milanesa a $9.200. La lista de opciones elegidas queda guardada aparte, para la cocina.

Es una decisión defendible — toda la matemática posterior lee un solo número — y está bien protegida: los precios salen siempre del catálogo del servidor, nunca de lo que manda el celular del comensal. Verifiqué que no hay forma de manipular el precio desde el cliente.

El costo es analítico. En el reporte de rentabilidad por producto, la misma milanesa aparece con precios unitarios distintos según lo que cada comensal le agregó. El precio promedio de venta del plato deja de ser comparable con el precio de la carta, y los ingresos por adicionales no se pueden medir como línea de negocio.

**Cambio propuesto.** Guardar el precio base y el total de adicionales como dos importes separados en la línea, además del unitario ya sumado. No cambia ningún cálculo existente y habilita medir cuánto factura el local por adicionales — que suele ser un margen alto.

---

### H9 — 🟡 Decimales de punto flotante en la frontera con Mercado Pago

El proyecto tiene una regla explícita: la plata se maneja siempre en enteros de centavos, nunca en decimales de punto flotante. Se respeta en todo el núcleo. Se rompe en dos puntos del adaptador de Mercado Pago: al armar el importe que se le envía a la pasarela y al leer la comisión que devuelve.

El riesgo concreto es bajo — el resultado se redondea a entero y los importes son chicos. Pero es exactamente el tipo de desvío de un centavo que aparece meses después en una conciliación y cuesta días encontrar.

**Cambio propuesto.** Convertir a decimal exacto en lugar de punto flotante en esos dos puntos. Es un cambio contenido en un archivo.

---

## 4. Lo que verifiqué y está bien

Vale decirlo explícito, porque en una auditoría lo que no se menciona queda en duda. Todo esto lo revisé y funciona como debe:

- ✅ Los importes son enteros de centavos, no admiten negativos y no se pueden sumar entre monedas distintas.
- ✅ El total de la comanda excluye correctamente las líneas anuladas.
- ✅ Los precios de los adicionales salen siempre del catálogo del servidor. No hay vector de manipulación desde el cliente — el endpoint por lote ni siquiera acepta el campo de precio.
- ✅ Las reglas de «elegí mínimo uno / máximo tres» de cada grupo de opciones se validan en el servidor antes de crear nada.
- ✅ Los pagos parciales acumulan bien: la comanda se salda recién cuando la suma de cobros confirmados cubre el total.
- ✅ Un cobro repetido por doble clic no cobra dos veces — hay clave de idempotencia.
- ✅ No se pueden agregar ítems a una comanda ya pagada.
- ✅ Hay límite de intentos de cobro por mesa: seis por minuto.
- ✅ La propina no cancela deuda de la comanda — sólo el importe de venta cuenta para saldarla.
- ✅ Un token de QR de un local que ya no existe se rechaza sin filtrar esa información.

---

## 5. Orden de trabajo propuesto

El criterio no es cuál es más fácil, sino cuál distorsiona más los números que se usan para decidir. H1 y H5 son el mismo arreglo; H2 y H3 tocan el mismo cálculo de saldo.

**1. Desacoplar la registración de la venta del estado de la mesa**
Resuelve H1 y H5, y elimina H6 por construcción. Hoy el sistema no puede registrar una venta sin liberar la mesa, y eso es una restricción falsa: son dos hechos distintos.
*Toca: `projection.py` · `payment/use_cases.py` · `order/use_cases.py`*

**2. Reconstruir el libro de ventas y conciliar contra la caja**
Antes de tocar código, medir el daño: correr la reconstrucción y comparar el total de ventas contra el total de cobros confirmados del mismo período. La diferencia es exactamente lo que H1 se comió hasta hoy.
*Control, no desarrollo. Da la magnitud real del problema.*

**3. Reservar saldo al iniciar un cobro y revalidar al confirmar**
Resuelve H2. Que un pago en curso descuente saldo disponible por unos minutos, y que el tope se vuelva a verificar cuando el webhook confirma. Dejar de mostrar el excedente como cero.
*Toca: `table_bill.py` · `pay_table_bill.py`*

**4. Que el saldo lea entradas menos salidas**
Resuelve H3. Cambio chico, mismo archivo que el paso anterior, así que conviene hacerlos juntos.
*Toca: `table_bill.py`*

**5. Alinear la base de la comisión y separar la de la propina**
Resuelve H4. Además obliga a tomar explícitamente una decisión de negocio que hoy está tomada por omisión.
*Toca: `payment/use_cases.py` · `mercadopago_gateway.py`*

**6. Cuenta de propinas a liquidar**
Resuelve H7. Es funcionalidad nueva más que corrección: el dato ya se guarda, falta acumularlo y darle circuito de salida.
*Alcance mayor. Merece su propia definición antes de codear.*

**7. Guardar precio base y adicionales por separado, y sacar los flotantes**
Resuelve H8 y H9. Ninguno de los dos cambia un número hoy; los dos evitan problemas de análisis y de conciliación más adelante.
*Toca: `order/entities.py` · `mercadopago_gateway.py`*

---

Auditoría de sólo lectura sobre `backend/app` en el commit `824a04e`. No se modificó ningún archivo. Cada hallazgo tiene su cadena de evidencia con archivo y línea, verificada contra el código en el árbol de trabajo — no contra la auditoría previa de `19c1ced`, que no cubre este circuito.
