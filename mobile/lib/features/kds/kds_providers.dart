import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/api_client.dart';
import '../../data/realtime/realtime_service.dart';
import '../floor/floor_providers.dart';
import '../order/order_dtos.dart';
import 'kds_repository.dart';

final kdsRepositoryProvider = Provider<KdsRepository>(
  (ref) => KdsRepository(ref.read(apiDioProvider)),
);

final tableNumbersProvider = FutureProvider<Map<String, int>>(
  (ref) => ref.read(kdsRepositoryProvider).tableNumbers(),
);

/// Cola del KDS por estación en vivo: carga + poll 20s + invalidación por SSE
/// `kds.changed` (espeja `use-kds-orders.ts`).
class KdsNotifier extends FamilyAsyncNotifier<List<Order>, Station> {
  Timer? _poll;
  StreamSubscription<RealtimeEvent>? _sse;

  @override
  Future<List<Order>> build(Station arg) async {
    ref.onDispose(() {
      _poll?.cancel();
      _sse?.cancel();
    });
    _poll = Timer.periodic(const Duration(seconds: 20), (_) => refresh());
    _sse = ref.read(realtimeServiceProvider).events('kds').listen((event) {
      if (event.name == 'kds.changed') refresh();
    });
    return ref.read(kdsRepositoryProvider).orders(arg);
  }

  Future<void> refresh() async {
    final data =
        await AsyncValue.guard(() => ref.read(kdsRepositoryProvider).orders(arg));
    if (data is AsyncData) state = data;
  }

  Future<void> advance(String orderId, String itemId, String action) async {
    await ref.read(kdsRepositoryProvider).advanceItem(orderId, itemId, action);
    await refresh();
  }
}

final kdsOrdersProvider =
    AsyncNotifierProvider.family<KdsNotifier, List<Order>, Station>(
  KdsNotifier.new,
);
