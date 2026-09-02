import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/api_error.dart';
import '../../l10n/strings.dart';
import '../../ui/glass_panel.dart';
import '../order/order_dtos.dart';
import 'kds_providers.dart';
import 'kds_ticket.dart';

/// Pantalla de cocina (Fase 2): tickets por ítem, más viejo primero, bump 1×1
/// (SENT→preparando→listo). En vivo por SSE `kds.changed` + poll 20s. Grilla
/// adaptativa (más columnas en tablet).
class KdsPage extends ConsumerStatefulWidget {
  const KdsPage({super.key, required this.station});

  final Station station;

  @override
  ConsumerState<KdsPage> createState() => _KdsPageState();
}

class _KdsPageState extends ConsumerState<KdsPage> {
  Timer? _tick;

  @override
  void initState() {
    super.initState();
    _tick = Timer.periodic(const Duration(seconds: 30), (_) {
      if (mounted) setState(() {});
    });
  }

  @override
  void dispose() {
    _tick?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final s = context.s;
    final async = ref.watch(kdsOrdersProvider(widget.station));
    final tables = ref.watch(tableNumbersProvider).valueOrNull ?? const {};

    return async.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (e, _) => Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Text(e is ApiError ? e.message : '$e'),
        ),
      ),
      data: (orders) {
        final tickets = kdsTickets(orders);
        if (tickets.isEmpty) {
          return ListView(
            children: [
              Padding(
                padding: const EdgeInsets.all(48),
                child: Center(child: Text(s.kdsEmpty)),
              ),
            ],
          );
        }
        return RefreshIndicator(
          onRefresh: () =>
              ref.read(kdsOrdersProvider(widget.station).notifier).refresh(),
          child: LayoutBuilder(
            builder: (ctx, c) {
              final cols = (c.maxWidth / 300).floor().clamp(1, 4);
              final width = (c.maxWidth - 16 - (cols - 1) * 12) / cols;
              return SingleChildScrollView(
                physics: const AlwaysScrollableScrollPhysics(),
                padding: const EdgeInsets.all(8),
                child: Wrap(
                  spacing: 12,
                  runSpacing: 12,
                  children: [
                    for (final t in tickets)
                      SizedBox(width: width, child: _card(s, t, tables)),
                  ],
                ),
              );
            },
          ),
        );
      },
    );
  }

  Widget _card(Strings s, KdsTicket t, Map<String, int> tables) {
    final scheme = Theme.of(context).colorScheme;
    final theme = Theme.of(context);
    final number = tables[t.order.tableId];
    final accent = t.isLate
        ? scheme.error
        : (t.isWarn ? const Color(0xFFE0A800) : scheme.primary);

    return GlassPanel(
      padding: const EdgeInsets.all(12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Row(
            children: [
              Text(
                number != null ? s.tableLabel(number) : s.kdsUnknownTable,
                style: theme.textTheme.titleMedium
                    ?.copyWith(fontWeight: FontWeight.w700),
              ),
              const Spacer(),
              if (t.minutes != null)
                Text('${t.minutes}′',
                    style: TextStyle(color: accent, fontWeight: FontWeight.w700)),
            ],
          ),
          if (t.isLate)
            Padding(
              padding: const EdgeInsets.only(top: 2),
              child: Text(
                s.kdsDelayed,
                style: TextStyle(
                    color: scheme.error, fontSize: 12, fontWeight: FontWeight.w600),
              ),
            ),
          const SizedBox(height: 8),
          Text(
            '${t.item.quantity}× ${t.item.name}',
            style: theme.textTheme.bodyLarge?.copyWith(fontWeight: FontWeight.w600),
          ),
          if (t.item.selectedOptions.isNotEmpty)
            Text(
              t.item.selectedOptions.map((o) => o.name).join(', '),
              style: TextStyle(color: scheme.onSurfaceVariant, fontSize: 12),
            ),
          if (t.item.note != null && t.item.note!.isNotEmpty)
            Text('› ${t.item.note}',
                style: TextStyle(color: scheme.onSurfaceVariant, fontSize: 12)),
          const SizedBox(height: 10),
          SizedBox(
            width: double.infinity,
            child: FilledButton(
              onPressed: () => _advance(
                t,
                t.item.status == ItemStatus.sent ? 'preparing' : 'ready',
              ),
              child: Text(t.item.status == ItemStatus.sent ? s.kdsStart : s.kdsReady),
            ),
          ),
        ],
      ),
    );
  }

  Future<void> _advance(KdsTicket t, String action) async {
    try {
      await ref
          .read(kdsOrdersProvider(widget.station).notifier)
          .advance(t.order.id, t.item.id, action);
    } on ApiError catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(e.message)));
      }
    }
  }
}
