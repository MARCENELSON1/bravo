import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/api_error.dart';
import '../../l10n/strings.dart';
import '../../theme/colors.dart';
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
        : (t.isWarn ? WellnodPalette.warn : scheme.primary);
    final overdue = t.isLate || t.isWarn;

    return Opacity(
      opacity: t.held ? 0.6 : 1, // en espera: se ve, no apura
      child: GlassPanel(
        blur: false, // un curso por ticket: sin blur por-tarjeta (perf)
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    '${number != null ? s.tableLabel(number) : s.kdsUnknownTable}'
                    ' · ${s.courseLabel(t.course)}',
                    style: theme.textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ),
                if (t.held)
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 8,
                      vertical: 3,
                    ),
                    decoration: BoxDecoration(
                      color: scheme.onSurfaceVariant.withValues(alpha: 0.15),
                      borderRadius: BorderRadius.circular(999),
                    ),
                    child: Text(
                      s.kdsOnHold,
                      style: TextStyle(
                        color: scheme.onSurfaceVariant,
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  )
                else if (t.minutes != null) ...[
                  // Además del color, un ícono de reloj cuando se está demorando
                  // (no depender solo del color por accesibilidad).
                  if (overdue) ...[
                    Icon(Icons.schedule, size: 15, color: accent),
                    const SizedBox(width: 3),
                  ],
                  Text(
                    '${t.minutes}′',
                    style: TextStyle(
                      color: accent,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ],
              ],
            ),
            if (t.isLate)
              Padding(
                padding: const EdgeInsets.only(top: 2),
                child: Text(
                  s.kdsDelayed,
                  style: TextStyle(
                    color: scheme.error,
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
            const SizedBox(height: 8),
            for (final it in t.items) ...[
              Text(
                '${it.quantity}× ${it.name}',
                style: theme.textTheme.bodyLarge?.copyWith(
                  fontWeight: FontWeight.w600,
                ),
              ),
              if (it.selectedOptions.isNotEmpty)
                Text(
                  it.selectedOptions.map((o) => o.name).join(', '),
                  style: TextStyle(
                    color: scheme.onSurfaceVariant,
                    fontSize: 12,
                  ),
                ),
              if (it.note != null && it.note!.isNotEmpty)
                Text(
                  '› ${it.note}',
                  style: TextStyle(
                    color: scheme.onSurfaceVariant,
                    fontSize: 12,
                  ),
                ),
              const SizedBox(height: 4),
            ],
            if (!t.held) ...[
              const SizedBox(height: 6),
              SizedBox(
                width: double.infinity,
                child: FilledButton(
                  // El curso entero: "Empezar" pone todo al fuego; "Listo" cuando
                  // la cocina terminó TODOS los platos del tiempo.
                  onPressed: () =>
                      _advanceCourse(t, t.canStart ? 'preparing' : 'ready'),
                  child: Text(t.canStart ? s.kdsStart : s.kdsReady),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Future<void> _advanceCourse(KdsTicket t, String action) async {
    try {
      HapticFeedback.mediumImpact();
      await ref
          .read(kdsOrdersProvider(widget.station).notifier)
          .advanceCourse(t.order.id, t.course, action);
    } on ApiError catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(e.message)));
      }
    }
  }
}
