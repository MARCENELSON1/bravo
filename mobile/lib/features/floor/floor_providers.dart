import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/api_client.dart';
import '../../data/realtime/realtime_service.dart';
import '../order/order_repository.dart';
import 'floor_dtos.dart';
import 'floor_repository.dart';

final floorRepositoryProvider = Provider<FloorRepository>(
  (ref) => FloorRepository(ref.read(apiDioProvider)),
);

final orderRepositoryProvider = Provider<OrderRepository>(
  (ref) => OrderRepository(ref.read(apiDioProvider)),
);

final realtimeServiceProvider = Provider<RealtimeService>(
  (ref) => RealtimeService(ref.read(apiDioProvider)),
);

final sectorsProvider = FutureProvider<List<Sector>>(
  (ref) => ref.read(floorRepositoryProvider).sectors(),
);

/// Estado del piso en vivo: carga inicial + poll de fallback 10s + invalidación
/// por SSE `floor.changed` (espeja `use-floor.ts`).
class FloorNotifier extends AsyncNotifier<List<FloorTable>> {
  Timer? _poll;
  StreamSubscription<String>? _sse;

  @override
  Future<List<FloorTable>> build() async {
    ref.onDispose(() {
      _poll?.cancel();
      _sse?.cancel();
    });
    _poll = Timer.periodic(const Duration(seconds: 10), (_) => refresh());
    _sse = ref.read(realtimeServiceProvider).events('floor').listen((event) {
      if (event == 'floor.changed') refresh();
    });
    return ref.read(floorRepositoryProvider).floor();
  }

  Future<void> refresh() async {
    final data = await AsyncValue.guard(
      () => ref.read(floorRepositoryProvider).floor(),
    );
    // No pisar datos buenos con un error transitorio del poll/SSE.
    if (data is AsyncData) state = data;
  }
}

final floorProvider =
    AsyncNotifierProvider<FloorNotifier, List<FloorTable>>(FloorNotifier.new);
