import 'package:flutter/material.dart';

import '../../l10n/strings.dart';
import '../../theme/colors.dart';
import '../../util/money.dart';
import 'floor_dtos.dart';
import 'floor_view.dart';

/// Acciones que se pueden disparar sobre una mesa sin entrar a la comanda.
enum QuickAction { serve, march, charge, bill, free, claim, open }

/// Long-press en la mesa → menú rápido. Devuelve la acción elegida (o null).
/// La primaria (lo que la mesa está pidiendo) va arriba y en ámbar.
Future<QuickAction?> showFloorQuickActions(
  BuildContext context, {
  required FloorTable table,
  required List<QuickAction> actions,
  required QuickAction? primary,
}) {
  final s = context.s;
  final v = floorView(table);
  final theme = Theme.of(context);
  final name = table.name ?? s.tableLabel(table.number);
  final subtitle = [
    s.floorState(v.status),
    if (v.minutes != null) s.minutesLabel(v.minutes!),
    if (v.totalAmount != null && v.totalAmount! > 0)
      formatMoney(v.totalAmount!, v.currency ?? 'ARS'),
  ].join(' · ');

  return showModalBottomSheet<QuickAction>(
    context: context,
    showDragHandle: true,
    builder: (ctx) => SafeArea(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(20, 0, 20, 8),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  name,
                  style: theme.textTheme.titleLarge?.copyWith(
                    fontWeight: FontWeight.w700,
                  ),
                ),
                Text(
                  subtitle,
                  style: TextStyle(
                    color: v.attention
                        ? WellnodPalette.warn
                        : theme.colorScheme.onSurfaceVariant,
                  ),
                ),
              ],
            ),
          ),
          for (final a in actions)
            ListTile(
              leading: Icon(
                _icon(a),
                color: a == primary ? WellnodPalette.warn : null,
              ),
              title: Text(
                _label(s, a),
                style: a == primary
                    ? const TextStyle(
                        color: WellnodPalette.warn,
                        fontWeight: FontWeight.w700,
                      )
                    : null,
              ),
              onTap: () => Navigator.of(ctx).pop(a),
            ),
          const SizedBox(height: 8),
        ],
      ),
    ),
  );
}

IconData _icon(QuickAction a) => switch (a) {
  QuickAction.serve => Icons.room_service_outlined,
  QuickAction.march => Icons.send,
  QuickAction.charge => Icons.payments_outlined,
  QuickAction.bill => Icons.receipt_long_outlined,
  QuickAction.free => Icons.event_available_outlined,
  QuickAction.claim => Icons.person_add_alt_1_outlined,
  QuickAction.open => Icons.open_in_new,
};

String _label(Strings s, QuickAction a) => switch (a) {
  QuickAction.serve => s.quickServe,
  QuickAction.march => s.quickMarch,
  QuickAction.charge => s.cobro,
  QuickAction.bill => s.floorRequestBill,
  QuickAction.free => s.floorFree,
  QuickAction.claim => s.claimTable,
  QuickAction.open => s.quickOpen,
};
