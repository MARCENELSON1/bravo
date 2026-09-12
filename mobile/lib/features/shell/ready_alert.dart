import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../auth/session_notifier.dart';
import '../../data/realtime/realtime_service.dart';
import '../../l10n/strings.dart';
import '../floor/floor_dtos.dart';
import '../floor/floor_providers.dart';
import '../order/comanda_lista_sheet.dart';

/// Decide si un evento SSE es un `order.ready` dirigido a este mozo, y extrae los
/// datos del modal. Función pura (testeable). Devuelve null si no aplica (otro
/// evento, otro mozo, o sin `order_id`).
({String orderId, int? tableNumber})? readyOrderFor(
  RealtimeEvent e,
  String userId,
) {
  if (e.name != 'order.ready') return null;
  if (e.data['waiter_id'] != userId) return null;
  final orderId = e.data['order_id'] as String?;
  if (orderId == null || orderId.isEmpty) return null;
  return (
    orderId: orderId,
    tableNumber: int.tryParse('${e.data['table_number'] ?? ''}'),
  );
}

/// Escucha global de `order.ready` (Fase 1): al mozo DUEÑO de la orden le muestra
/// un banner "Mesa N lista · Ver" —esté en la tab que esté— que abre el modal con
/// la comanda. Filtra por `waiter_id == userId` (solo al dueño; cocina no lo ve).
class ReadyAlert extends ConsumerStatefulWidget {
  const ReadyAlert({super.key, required this.child});
  final Widget child;

  @override
  ConsumerState<ReadyAlert> createState() => _ReadyAlertState();
}

class _ReadyAlertState extends ConsumerState<ReadyAlert> {
  StreamSubscription<RealtimeEvent>? _sub;

  /// Orden del banner visible. Si esa comanda deja de tener un curso listo
  /// (la sirvió el propio mozo desde la comanda, o alguien más), el aviso se
  /// descarta solo: si no, queda pegado y su "Marcar servido" falla.
  String? _bannerOrderId;

  @override
  void initState() {
    super.initState();
    _sub = ref.read(realtimeServiceProvider).events('floor').listen(_onEvent);
  }

  void _onEvent(RealtimeEvent e) {
    if (!mounted) return;
    final session = ref.read(sessionProvider);
    if (session is! SessionAuthenticated) return;
    final ready = readyOrderFor(e, session.session.userId);
    if (ready == null) return;
    _showBanner(ready.orderId, ready.tableNumber);
  }

  /// Ya no hay nada listo en esa mesa → sacar el aviso.
  void _dismissIfServed(List<FloorTable> tables) {
    final id = _bannerOrderId;
    if (id == null) return;
    for (final t in tables) {
      if (t.activeOrder?.id == id) {
        if (t.activeOrder!.readyCourse != null) return; // sigue habiendo listo
        break;
      }
    }
    _bannerOrderId = null;
    ScaffoldMessenger.of(context).hideCurrentMaterialBanner();
  }

  void _showBanner(String orderId, int? tableNumber) {
    final s = context.s;
    final messenger = ScaffoldMessenger.of(context);
    _bannerOrderId = orderId;
    final scheme = Theme.of(context).colorScheme;
    messenger.showMaterialBanner(
      MaterialBanner(
        leading: Icon(Icons.room_service_outlined, color: scheme.primary),
        content: Text(
          tableNumber != null
              ? s.readyBannerTitle(tableNumber)
              : s.readyBannerTitleNoTable,
        ),
        actions: [
          TextButton(
            onPressed: () {
              _bannerOrderId = null;
              messenger.hideCurrentMaterialBanner();
            },
            child: Text(s.readyBannerDismiss),
          ),
          FilledButton(
            onPressed: () {
              _bannerOrderId = null;
              messenger.hideCurrentMaterialBanner();
              ComandaListaSheet.show(
                context,
                orderId: orderId,
                tableNumber: tableNumber,
              );
            },
            child: Text(s.readyBannerAction),
          ),
        ],
      ),
    );
  }

  @override
  void dispose() {
    _sub?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    // El piso es la fuente en vivo: en cuanto la mesa deja de tener un curso
    // listo, el aviso se va solo.
    ref.listen(floorProvider, (_, next) {
      final tables = next.valueOrNull;
      if (tables != null && mounted) _dismissIfServed(tables);
    });
    return widget.child;
  }
}
