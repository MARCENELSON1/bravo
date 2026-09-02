import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/api_error.dart';
import '../../l10n/strings.dart';
import '../../ui/app_background.dart';
import '../../ui/glass_panel.dart';
import '../../util/money.dart';
import 'inventory_repository.dart';

/// Insumos (Fase 6, consulta): stock y costo por insumo, los bajo-mínimo primero.
class InsumosPage extends ConsumerWidget {
  const InsumosPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = context.s;
    final async = ref.watch(ingredientsProvider);
    return Scaffold(
      backgroundColor: Colors.transparent,
      appBar: AppBar(
        title: Text(s.insumosTitle),
        backgroundColor: Colors.transparent,
      ),
      body: Stack(
        children: [
          const AppBackground(),
          SafeArea(
            child: async.when(
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (e, _) => Center(
                child: Padding(
                  padding: const EdgeInsets.all(24),
                  child: Text(e is ApiError ? e.message : '$e'),
                ),
              ),
              data: (items) {
                if (items.isEmpty) return Center(child: Text(s.insumosEmpty));
                final sorted = [...items]..sort((a, b) {
                    if (a.isBelowMin == b.isBelowMin) return 0;
                    return a.isBelowMin ? -1 : 1;
                  });
                return ListView(
                  padding: const EdgeInsets.all(16),
                  children: [
                    GlassPanel(
                      padding: const EdgeInsets.symmetric(vertical: 4),
                      child: Material(
                        type: MaterialType.transparency,
                        child: Column(
                          children: [
                            for (var i = 0; i < sorted.length; i++) ...[
                              if (i > 0) const Divider(height: 1),
                              _row(context, s, sorted[i]),
                            ],
                          ],
                        ),
                      ),
                    ),
                  ],
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _row(BuildContext context, Strings s, Ingredient ing) {
    final scheme = Theme.of(context).colorScheme;
    return ListTile(
      title: Row(
        children: [
          Flexible(child: Text(ing.name)),
          if (ing.isBelowMin) ...[
            const SizedBox(width: 8),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
              decoration: BoxDecoration(
                color: scheme.error.withValues(alpha: 0.15),
                borderRadius: BorderRadius.circular(999),
              ),
              child: Text(s.insumosBelowMin,
                  style: TextStyle(color: scheme.error, fontSize: 11)),
            ),
          ],
        ],
      ),
      subtitle: Text('${s.insumosStock}: ${ing.stockQty} ${ing.unit} · mín ${ing.minQty}'),
      trailing: Text(formatMoney(ing.unitCostAmount, ing.currency)),
    );
  }
}
