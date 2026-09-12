import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../features/floor/floor_providers.dart';
import '../../features/order/order_providers.dart';
import 'sync_providers.dart';
import 'sync_service.dart';

/// Servicio de sync (drena la cola al reconectar). Al drenar, invalida las
/// comandas abiertas y refresca el piso para reconciliar con el server.
final syncServiceProvider = Provider<SyncService>((ref) {
  final service = SyncService(
    queue: ref.read(syncQueueProvider),
    repo: ref.read(orderRepositoryProvider),
    onDrained: () {
      ref.invalidate(orderControllerProvider);
      ref.read(floorProvider.notifier).refresh();
    },
  );
  ref.onDispose(service.dispose);
  return service;
});
