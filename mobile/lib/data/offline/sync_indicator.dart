import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../l10n/strings.dart';
import 'sync_providers.dart';

/// Chip que muestra cuántas operaciones quedan por sincronizar (modo
/// contingencia). Se oculta cuando la cola está vacía.
class SyncIndicator extends ConsumerWidget {
  const SyncIndicator({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final queue = ref.watch(syncQueueProvider);
    return ValueListenableBuilder<int>(
      valueListenable: queue.count,
      builder: (context, count, _) {
        if (count == 0) return const SizedBox.shrink();
        final scheme = Theme.of(context).colorScheme;
        return Padding(
          padding: const EdgeInsets.only(right: 12),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(Icons.cloud_off_outlined, size: 16, color: scheme.onSurfaceVariant),
              const SizedBox(width: 4),
              Text(
                context.s.pendingSync(count),
                style: TextStyle(fontSize: 12, color: scheme.onSurfaceVariant),
              ),
            ],
          ),
        );
      },
    );
  }
}
