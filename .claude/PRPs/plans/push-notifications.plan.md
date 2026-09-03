# Plan: Push real (APNs/FCM) — avisos con la app cerrada (Fase 4)

## Summary
Que los avisos operativos que hoy llegan solo con la **app abierta** (SSE) —"Mesa X lista" (`order.ready`, Fase 1) y "Te asignaron la Mesa X" (`table.assigned`, Fase 3)— lleguen también como **push** con la app cerrada/en background. Se aísla en un **port `NotificationService`** con adapter real **FCM** (detrás de un flag) + null-object para dev, calcando el patrón de `EmailSender`. FCM entrega a **iOS (por APNs) y Android** con un solo proveedor. Depende de Fase 1 y Fase 3 (los eventos ya se emiten con el `waiter_id` destinatario).

## User Story
Como **mozo** con la app en el bolsillo (pantalla apagada), quiero **que me llegue una notificación cuando mi comanda está lista o me asignan una mesa**, para **no tener que estar mirando la app** en pleno servicio.

## Problem → Solution
Hoy `order.ready`/`table.assigned` van solo por el **EventBus→SSE**, que requiere un stream abierto (app en primer plano). Con la app cerrada, no llega nada (el fallback es el Piso pasivo). → Un `NotificationService` que, en el **mismo punto** donde hoy se hace `event_bus.publish(...)`, manda además un push al `waiter_id` destinatario. El tap del push **abre el modal de la comanda** (deep-link), reusando la lógica de `ReadyAlert` (`readyOrderFor`).

## Metadata
- **Complexity**: XL (backend: port+adapter+flag, tabla+repo+migración, endpoint, wiring en 3 use cases; mobile: paquetes Firebase + config nativa iOS/Android + registro de token + handler de tap)
- **Source PRD**: `.claude/PRPs/prds/comanda-lista-y-asignacion.prd.md` — Fase 4
- **Depends**: Fase 1 (`order.ready`), Fase 3 (`table.assigned`)
- **Estimated Files**: ~18 backend/mobile + config nativa

---

## ⚠️ Lo que tenés que setear VOS (dependencias externas)
El código lo escribo yo; esto no lo puedo hacer por vos y **el push no se valida sin dispositivo real** (no anda en el simulador):

1. **Proyecto Firebase** (una sola vez) → habilitar **Cloud Messaging**.
2. **iOS:** subir a Firebase tu **APNs Auth Key** (`.p8`) del Apple Developer (Team X9SV6U45YM). Bajar **`GoogleService-Info.plist`** → va en `mobile/ios/Runner/`.
3. **Android:** bajar **`google-services.json`** → va en `mobile/android/app/`.
4. **Backend:** un **service-account JSON** de ese proyecto Firebase (para que el server mande push por la API HTTP v1) → como secret/env en Railway (`FCM_CREDENTIALS_*`).

Sin (1)–(3) la app compila pero **no obtiene token** (el push queda inerte); sin (4) el server no envía (queda en `PUSH_PROVIDER=none`, no-op). Por eso el plan separa lo que se puede construir/deployar ya (no-op seguro) de lo que necesita tu setup.

---

## Decisiones de diseño (recomendación)

| Decisión | Recomendación | Por qué |
|---|---|---|
| **Proveedor** | **FCM único** (`PUSH_PROVIDER=fcm\|none`) | FCM entrega a iOS (vía APNs) **y** Android → un solo adapter, no dos |
| **Enganche del envío** | **Inyectar `NotificationService`** en los use cases, al lado del `event_bus.publish(...)` | El EventBus HOY es solo-SSE (no hay patrón de subscriber server-side; un evento sin suscriptor se pierde). Inyectar es lo alineado con el patrón actual |
| **Port** | Un método `notify_user(tenant_id, user_id, PushMessage)` | Fino y genérico; el use case arma el texto (ES), el adapter resuelve tokens + envía |
| **Resolver destinatario** | `device_tokens.user_id == waiter_id` (el `waiter_id` del evento **es** un `user_id`) + `tenant_id` | Ya lo tenemos en el payload |
| **Deep-link del tap** | Reusar `readyOrderFor` + `ComandaListaSheet.show` (no crear ruta go_router) | El modal ya se abre así desde `ReadyAlert`; el tap reproduce ese efecto |
| **Default seguro** | `PUSH_PROVIDER=none` (`NullPushService`, no-op) | Deploy sin riesgo hasta que prendas FCM |

---

## Mandatory Reading

| Priority | File | Lines | Why |
|---|---|---|---|
| P0 | `backend/app/container.py` | 418-435 | `email_sender = providers.Selector(...)` = molde EXACTO de `push_service` |
| P0 | `backend/app/domain/identity/ports.py` | 80-90 | `EmailSender(ABC)` = molde del port |
| P0 | `backend/app/infrastructure/email/console_sender.py` | — | `ConsoleEmailSender` = molde del null/dev adapter |
| P0 | `backend/app/config.py` | 45-55, 191-222 | Flag `email_transport` + validación fail-fast prod (calcar para `push_provider`) |
| P0 | `backend/app/application/order/use_cases.py` | 304-316, 362-398 | `_order_ready` + `AdvanceItem/AdvanceOrder._publish_ready_if_complete` (dónde notificar) |
| P0 | `backend/app/application/payment/use_cases.py` | 108-119, 414-447 | `_table_assigned` + `ConfirmGatewayPayment._march_prepaid_order` (dónde notificar) |
| P0 | `backend/app/infrastructure/persistence/models.py` | 132-147 | `RefreshTokenORM` = molde de `DeviceTokenORM` (tenant+user scoped) |
| P0 | `backend/app/infrastructure/persistence/refresh_token_repo.py` | 1-47 | Molde del repo SQLAlchemy |
| P0 | `backend/alembic/versions/0043_taxjar_credentials.py` | 1-54 | Molde de migración: crear tabla tenant-scoped + RLS |
| P1 | `backend/app/presentation/api/v1/me.py` | 1-31 | Molde de router autenticado (`POST /devices`) |
| P1 | `backend/app/main.py` | 80-115, 132 | `include_router` + wiring por paquete (auto) |
| P0 | `mobile/lib/features/shell/ready_alert.dart` | 15-25, 56-82 | `readyOrderFor` + `ComandaListaSheet.show` (a reusar en el tap) |
| P0 | `mobile/lib/features/shell/app_scaffold.dart` | 36-74 | Dónde registrar el token (sesión autenticada) |
| P0 | `mobile/lib/main.dart` | 11-35 | `Firebase.initializeApp` + arranque del push service |
| P1 | `mobile/lib/api/api_client.dart` | 32-41 | `apiDioProvider` (dio autenticado) para `POST /devices` |
| P1 | `mobile/lib/features/order/comanda_lista_sheet.dart` | 19-27 | El modal destino del deep-link |

---

## Files to Change / Create

**Backend**
| File | Action | Qué |
|---|---|---|
| `app/domain/notification/ports.py` | CREATE | `NotificationService(ABC)` + `PushMessage` |
| `app/domain/notification/repository.py` | CREATE | `DeviceTokenRepository(ABC)` |
| `app/domain/notification/entities.py` | CREATE | `DeviceToken` |
| `app/infrastructure/notification/null_service.py` | CREATE | `NullPushService` (no-op, default) |
| `app/infrastructure/notification/fcm_service.py` | CREATE | `FcmPushService` (FCM HTTP v1; resuelve tokens + envía) |
| `app/infrastructure/persistence/models.py` | UPDATE | `DeviceTokenORM` (molde `RefreshTokenORM`) |
| `app/infrastructure/persistence/device_token_repo.py` | CREATE | `SqlAlchemyDeviceTokenRepository` |
| `alembic/versions/0053_device_tokens.py` | CREATE | Tabla `device_tokens` + RLS (molde 0043) |
| `app/application/notification/use_cases.py` | CREATE | `RegisterDeviceToken` |
| `app/presentation/api/v1/devices.py` | CREATE | `POST /devices` (+ schema) |
| `app/main.py` | UPDATE | `include_router(devices.router)` |
| `app/config.py` | UPDATE | `push_provider` + `fcm_*` + fail-fast prod |
| `app/container.py` | UPDATE | `device_token_repository`, `push_service = Selector(...)`, inyectar en use cases |
| `app/application/order/use_cases.py` | UPDATE | `AdvanceItem/AdvanceOrder`: `notify_user` tras el publish de `order.ready` |
| `app/application/payment/use_cases.py` | UPDATE | `ConfirmGatewayPayment`: `notify_user` tras `table.assigned` |
| `pyproject.toml` | UPDATE | dep `google-auth` (token OAuth del service account) |
| tests | CREATE | unit `FcmPushService` (fake HTTP) + integración `POST /devices` + que el push se dispara (fake service espía) |

**Mobile**
| File | Action | Qué |
|---|---|---|
| `pubspec.yaml` | UPDATE | `firebase_core` + `firebase_messaging` |
| `lib/data/push/push_service.dart` | CREATE | init FCM, permiso, token, listeners (foreground/tap/terminated) |
| `lib/data/push/device_repository.dart` | CREATE | `POST /devices` |
| `lib/main.dart` | UPDATE | `Firebase.initializeApp` + background handler |
| `lib/features/shell/app_scaffold.dart` | UPDATE | registrar token al autenticarse + montar el handler de tap |
| `lib/l10n/strings.dart` | UPDATE | textos del push (ES/EN) — o reusar los de `ReadyAlert` |
| `ios/Runner/*` | UPDATE | entitlement `aps-environment`, capability Push, `AppDelegate` (+ `GoogleService-Info.plist` que ponés vos) |
| `android/*` | UPDATE | plugin gradle google-services, permiso `POST_NOTIFICATIONS` (+ `google-services.json` que ponés vos) |

---

## Step-by-Step (por tanda)

### Tanda A — Backend base (100% construible/deployable YA, no-op seguro)
1. **Port + entidades**: `NotificationService.notify_user(*, tenant_id, user_id, message: PushMessage)`; `PushMessage(title, body, data: dict[str,str])`; `DeviceToken`; `DeviceTokenRepository` (`register`, `list_for_user`).
2. **Null adapter**: `NullPushService` (loguea y listo) — default.
3. **Tabla + repo + migración**: `DeviceTokenORM` (molde `RefreshTokenORM`), `SqlAlchemyDeviceTokenRepository` (molde `refresh_token_repo`), `0053_device_tokens` con RLS (molde `0043`, head `0052`). `register` es **upsert por token** (un device re-registra sin duplicar).
4. **Endpoint**: `POST /devices` `{token, platform}` → `RegisterDeviceToken` (usa `identity.tenant_id`+`user_id`). Molde `me.py`.
5. **Wiring + enganche**: `push_service = providers.Selector(config.push_provider, none=NullPushService, fcm=FcmPushService)`; inyectar en `AdvanceItem`/`AdvanceOrder`/`ConfirmGatewayPayment`; llamar `notify_user` tras el publish (title/body en ES: "Mesa N lista", "Te asignaron la Mesa N"; `data` con `kind`+`order_id`).
6. **Tests**: fake `NotificationService` espía → el push se dispara con el `waiter_id` correcto al pasar a READY / al asignar; integración `POST /devices` registra. `PUSH_PROVIDER=none` no rompe nada.

### Tanda B — Backend adapter FCM real (construible; se valida cuando pongas credenciales)
7. `FcmPushService(device_tokens, credentials)`: resuelve tokens de `(tenant_id, user_id)`, arma el mensaje FCM (notification + data), obtiene el access-token OAuth del service-account (`google-auth`), `POST https://fcm.googleapis.com/v1/projects/{proj}/messages:send` por token; limpia tokens muertos (404/`UNREGISTERED` → borrar). `config.py`: `push_provider`, `fcm_project_id`, `fcm_credentials_path` (o JSON inline) + fail-fast prod. Unit test con HTTP fake.

### Tanda C — Mobile (código construible; queda inerte sin tus archivos nativos)
8. Paquetes `firebase_core`+`firebase_messaging`; `Firebase.initializeApp` en `main.dart` + `FirebaseMessaging.onBackgroundMessage`.
9. `PushService`: pedir permiso, obtener el FCM token, `onTokenRefresh`; listeners `onMessage` (foreground — opcional, ya está el SSE), `onMessageOpenedApp` + `getInitialMessage` (tap → deep-link).
10. `DeviceRepository.register(token, platform)` → `POST /devices`; registrar **al autenticarse** (en `AppScaffold`, con sesión).
11. **Tap → modal**: parsear `message.data` (`kind`, `order_id`, `table_number`), reusar la lógica de `readyOrderFor`, y `ComandaListaSheet.show(...)`. Si el contexto aún no está, guardar el evento pendiente y abrirlo cuando `/app` monte.

### Tanda D — Tu setup + validación en device real
12. Vos: Firebase project + APNs key + `GoogleService-Info.plist` + `google-services.json` + service-account en Railway (`PUSH_PROVIDER=fcm`). Config nativa iOS (capability/entitlement/AppDelegate) y Android (gradle/permiso) — te dejo el paso a paso.
13. Validación en iPhone real (TestFlight): app cerrada → cocina marca "Listo" → llega el push → tap → abre el modal.

---

## Testing Strategy
- **Unit**: `FcmPushService` (fake HTTP: arma el request correcto, borra token muerto); `RegisterDeviceToken` (upsert).
- **Integration**: `POST /devices` registra el token del user; con un fake `NotificationService` inyectado, avanzar una orden a READY dispara `notify_user(user_id=waiter)`; confirmar un pago de autoservicio dispara `notify_user` del asignado.
- **No-regresión**: `PUSH_PROVIDER=none` → todo sigue igual (SSE intacto).
- **Manual (device real, Tanda D)**: app cerrada → push llega → tap abre el modal correcto.

## Validation Commands
```bash
cd backend && ruff check app tests && alembic upgrade head && pytest -q
cd mobile && flutter analyze && flutter test   # (sin los archivos nativos, la app compila; el push queda inerte)
```

## Acceptance Criteria
- [ ] `POST /devices` registra/actualiza el token del user (upsert, tenant+user scoped, RLS).
- [ ] Al pasar una orden a READY / auto-asignar, el backend llama `notify_user` con el `waiter_id` correcto (verificado con fake).
- [ ] `PUSH_PROVIDER=none` = no-op (deploy seguro); `fcm` envía por FCM.
- [ ] Mobile: registra el token al loguearse; el tap del push abre `ComandaListaSheet`.
- [ ] Migración 0053 reversible; RLS en `device_tokens`. `ruff`/`pytest`/`flutter` verdes.
- [ ] (Tanda D) push real llega a un iPhone con la app cerrada.

## Risks
| Risk | Mitigation |
|---|---|
| Sin setup Firebase el mobile no obtiene token | Tanda A/B deployan no-op; el código mobile compila inerte hasta tus archivos |
| EventBus no persiste (evento sin suscriptor se pierde) | No usamos el bus para push: `notify_user` se llama directo en el use case |
| Tokens muertos acumulan | El adapter FCM borra el token ante `UNREGISTERED`/404 |
| Multi-worker (bus in-memory) | El push NO depende del bus → funciona igual con varios workers |
| APNs/FCM config nativa iOS delicada | Paso a paso en Tanda D; validación en device real |

## Notes
- El push es **aditivo** al SSE: con la app abierta sigue el aviso en vivo (Fase 1); el push cubre app cerrada.
- Reusa los dos eventos ya emitidos (Fase 1 + Fase 3) sin tocarlos: solo se agrega la llamada `notify_user` al lado.
- Recomendación de arranque: **implemento Tanda A ya** (backend base, no-op, deployable + testeado) y la B (adapter FCM detrás del flag), mientras vos hacés el setup de Firebase; después C (mobile) + D (validación).

---

*Generated: 2026-09-03 · Status: DRAFT — needs approval*
