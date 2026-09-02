import 'package:flutter/material.dart';

import '../../l10n/strings.dart';
import '../../theme/colors.dart';
import '../../ui/glass_panel.dart';
import '../../util/money.dart';
import 'floor_dtos.dart';
import 'floor_view.dart';

class TableCard extends StatelessWidget {
  const TableCard({
    super.key,
    required this.table,
    required this.onOpen,
    this.onBill,
  });

  final FloorTable table;
  final VoidCallback onOpen;
  final VoidCallback? onBill;

  @override
  Widget build(BuildContext context) {
    final s = context.s;
    final v = floorView(table);
    final scheme = Theme.of(context).colorScheme;
    final accent = _accent(v.status, scheme);

    return InkWell(
      onTap: onOpen,
      borderRadius: BorderRadius.circular(16),
      child: GlassPanel(
        blur: false, // grilla de mesas: sin blur por-tarjeta (perf)
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            Row(
              children: [
                Text(
                  table.name ?? '${table.number}',
                  style: Theme.of(context)
                      .textTheme
                      .titleLarge
                      ?.copyWith(fontWeight: FontWeight.w700),
                ),
                const Spacer(),
                if (v.pax != null)
                  Text(s.paxLabel(v.pax!),
                      style: TextStyle(color: scheme.onSurfaceVariant)),
              ],
            ),
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
              decoration: BoxDecoration(
                color: accent.withValues(alpha: 0.18),
                borderRadius: BorderRadius.circular(999),
              ),
              child: Text(
                s.floorState(v.status),
                style: TextStyle(
                    color: accent, fontSize: 12, fontWeight: FontWeight.w600),
              ),
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                if (v.totalAmount != null && v.totalAmount! > 0)
                  Text(
                    formatMoney(v.totalAmount!, v.currency ?? 'ARS'),
                    style: Theme.of(context).textTheme.bodyMedium,
                  ),
                const Spacer(),
                if (v.minutes != null)
                  Text(s.minutesLabel(v.minutes!),
                      style: TextStyle(color: scheme.onSurfaceVariant)),
              ],
            ),
            if (v.waiterName != null) ...[
              const SizedBox(height: 2),
              Text(v.waiterName!,
                  style: TextStyle(color: scheme.onSurfaceVariant, fontSize: 12)),
            ],
            if (onBill != null) ...[
              const SizedBox(height: 4),
              Align(
                alignment: Alignment.centerRight,
                child: TextButton(
                  onPressed: onBill,
                  style: TextButton.styleFrom(padding: EdgeInsets.zero),
                  child: Text(s.floorRequestBill),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Color _accent(FloorStatus status, ColorScheme scheme) {
    switch (status) {
      case FloorStatus.toServe:
        return WellnodPalette.warn; // ámbar de atención
      case FloorStatus.toCharge:
        return scheme.primary;
      case FloorStatus.served:
        return const Color(0xFF10B981); // esmeralda
      case FloorStatus.free:
      case FloorStatus.open:
      case FloorStatus.inKitchen:
      case FloorStatus.closed:
        return scheme.onSurfaceVariant;
    }
  }
}
