import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../l10n/strings.dart';
import '../../ui/app_background.dart';
import '../../ui/glass_panel.dart';
import '../../ui/state_views.dart';
import '../../util/money.dart';
import 'invoice_repository.dart';

/// Comprobantes (Fase 6, consulta): lista de comprobantes fiscales emitidos.
class ComprobantesPage extends ConsumerWidget {
  const ComprobantesPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = context.s;
    final async = ref.watch(invoicesProvider);
    return Scaffold(
      backgroundColor: Colors.transparent,
      appBar: AppBar(
        title: Text(s.comprobantesTitle),
        backgroundColor: Colors.transparent,
      ),
      body: Stack(
        children: [
          const AppBackground(),
          SafeArea(
            child: async.when(
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (e, _) => ErrorView(
                error: e,
                onRetry: () => ref.invalidate(invoicesProvider),
              ),
              data: (invoices) {
                Future<void> refresh() async =>
                    ref.invalidate(invoicesProvider);
                if (invoices.isEmpty) {
                  return RefreshIndicator(
                    onRefresh: refresh,
                    child: ListView(
                      physics: const AlwaysScrollableScrollPhysics(),
                      children: [
                        SizedBox(
                            height: 280,
                            child: EmptyView(message: s.comprobantesEmpty)),
                      ],
                    ),
                  );
                }
                return RefreshIndicator(
                  onRefresh: refresh,
                  child: ListView(
                    physics: const AlwaysScrollableScrollPhysics(),
                    padding: const EdgeInsets.all(16),
                    children: [
                      GlassPanel(
                        padding: const EdgeInsets.symmetric(vertical: 4),
                        child: Material(
                          type: MaterialType.transparency,
                          child: Column(
                            children: [
                              for (var i = 0; i < invoices.length; i++) ...[
                                if (i > 0) const Divider(height: 1),
                                _tile(invoices[i]),
                              ],
                            ],
                          ),
                        ),
                      ),
                    ],
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _tile(Invoice inv) {
    final label = inv.number == null
        ? inv.type
        : '${inv.type} ${inv.pointOfSale ?? ''}-${inv.number}';
    final subtitle = inv.cae == null ? inv.status : 'CAE ${inv.cae} · ${inv.status}';
    return ListTile(
      title: Text(label),
      subtitle: Text(subtitle),
      trailing: Text(formatMoney(inv.total, inv.currency)),
    );
  }
}
