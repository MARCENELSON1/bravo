import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../theme/theme_controller.dart';
import 'sync_queue.dart';

/// Provider de la cola (sin dependencias del feature order, para que
/// `order_providers` lo pueda importar sin ciclo). El `SyncService` vive aparte.
final syncQueueProvider = Provider<SyncQueue>(
  (ref) => SyncQueue(ref.read(sharedPreferencesProvider)),
);
