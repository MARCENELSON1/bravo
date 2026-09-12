import 'package:flutter/material.dart';

import '../../l10n/strings.dart';
import '../../theme/colors.dart';
import '../../ui/glass_panel.dart';
import '../../util/money.dart';
import 'floor_dtos.dart';
import 'floor_view.dart';

/// Card de una mesa en el plano. La **atención** (para servir / a cobrar)
/// domina: franja y tinte ámbar, minutos grandes; lo tranquilo se atenúa y
/// lo libre casi desaparece. `flash` = acaba de pasar a pedir atención → un
/// pulso breve para que se note el cambio (llega por SSE, sin que nadie mire).
class TableCard extends StatelessWidget {
  const TableCard({
    super.key,
    required this.table,
    required this.onOpen,
    this.onLongPress,
    this.onBill,
    this.onFree,
    this.flash = false,
  });

  final FloorTable table;
  final VoidCallback onOpen;
  final VoidCallback? onLongPress;
  final VoidCallback? onBill;
  // Autoservicio ya pago: "Liberar" en vez de "Cobrar" (no se cobra de nuevo).
  final VoidCallback? onFree;
  final bool flash;

  @override
  Widget build(BuildContext context) {
    final s = context.s;
    final v = floorView(table);
    final theme = Theme.of(context);
    final scheme = theme.colorScheme;
    final accent = _accent(v.status, scheme);
    final attention = v.attention;
    final free = v.status == FloorStatus.free;
    final reduceMotion = MediaQuery.of(context).disableAnimations;

    final card = GlassPanel(
      blur: false, // grilla de mesas: sin blur por-tarjeta (perf)
      padding: EdgeInsets.zero,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 280),
        curve: Curves.easeOut,
        padding: EdgeInsets.fromLTRB(attention ? 12 : 14, 12, 12, 12),
        decoration: BoxDecoration(
          color: attention ? accent.withValues(alpha: 0.12) : null,
          border: attention
              ? Border(left: BorderSide(color: accent, width: 4))
              : null,
          boxShadow: flash && !reduceMotion
              ? [
                  BoxShadow(
                    color: accent.withValues(alpha: 0.55),
                    blurRadius: 22,
                    spreadRadius: 1,
                  ),
                ]
              : null,
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: Text(
                    table.name ?? '${table.number}',
                    style: theme.textTheme.titleLarge?.copyWith(
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ),
                // Minutos: prominentes cuando pide atención, discretos si no.
                if (v.minutes != null)
                  attention
                      ? Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 8,
                            vertical: 3,
                          ),
                          decoration: BoxDecoration(
                            color: accent.withValues(alpha: 0.22),
                            borderRadius: BorderRadius.circular(999),
                          ),
                          child: Text(
                            s.minutesLabel(v.minutes!),
                            style: TextStyle(
                              color: accent,
                              fontWeight: FontWeight.w800,
                              fontSize: 13,
                              fontFeatures: const [
                                FontFeature.tabularFigures(),
                              ],
                            ),
                          ),
                        )
                      : Text(
                          s.minutesLabel(v.minutes!),
                          style: TextStyle(
                            color: scheme.onSurfaceVariant,
                            fontFeatures: const [FontFeature.tabularFigures()],
                          ),
                        ),
              ],
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 8,
                    vertical: 3,
                  ),
                  decoration: BoxDecoration(
                    color: accent.withValues(alpha: attention ? 0.28 : 0.16),
                    borderRadius: BorderRadius.circular(999),
                  ),
                  child: Text(
                    s.floorState(v.status),
                    style: TextStyle(
                      color: accent,
                      fontSize: 12,
                      fontWeight: attention ? FontWeight.w800 : FontWeight.w600,
                    ),
                  ),
                ),
                if (v.pax != null) ...[
                  const SizedBox(width: 6),
                  Text(
                    s.paxLabel(v.pax!),
                    style: TextStyle(
                      color: scheme.onSurfaceVariant,
                      fontSize: 12,
                    ),
                  ),
                ],
              ],
            ),
            if (v.totalAmount != null && v.totalAmount! > 0) ...[
              const SizedBox(height: 8),
              Text(
                formatMoney(v.totalAmount!, v.currency ?? 'ARS'),
                style: theme.textTheme.bodyMedium?.copyWith(
                  fontWeight: FontWeight.w600,
                  fontFeatures: const [FontFeature.tabularFigures()],
                ),
              ),
            ],
            if (v.waiterName != null) ...[
              const SizedBox(height: 2),
              Text(
                v.waiterName!,
                style: TextStyle(color: scheme.onSurfaceVariant, fontSize: 12),
              ),
            ],
            if (onFree != null) ...[
              const SizedBox(height: 4),
              Align(
                alignment: Alignment.centerRight,
                child: TextButton(
                  onPressed: onFree,
                  style: TextButton.styleFrom(padding: EdgeInsets.zero),
                  child: Text(s.floorFree),
                ),
              ),
            ] else if (onBill != null) ...[
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

    return AnimatedScale(
      scale: flash && !reduceMotion ? 1.03 : 1,
      duration: const Duration(milliseconds: 280),
      curve: Curves.easeOut,
      child: Opacity(
        opacity: free ? 0.55 : 1,
        // La tarjeta es un botón dibujado a mano: sin esto VoiceOver la lee como
        // una pila de textos sueltos y no dice que se puede tocar. El rótulo junta
        // lo que el mozo ve de un vistazo —mesa, estado y minutos— en una sola
        // frase, que es como la escucha quien no puede mirarla.
        child: Semantics(
          button: true,
          label: _semanticLabel(context, s, v),
          child: InkWell(
            onTap: onOpen,
            onLongPress: onLongPress,
            borderRadius: BorderRadius.circular(16),
            child: card,
          ),
        ),
      ),
    );
  }

  /// Color real por estado (antes "en cocina / abierta / libre" eran el mismo
  /// gris): ámbar = atención, esmeralda = servida, primario = a cobrar.
  /// Lo que VoiceOver dice de la tarjeta, en una frase.
  ///
  /// El orden importa: primero qué mesa es, después en qué estado está y recién
  /// al final el detalle. Quien escucha no puede saltear con la vista, así que lo
  /// que decide la acción va adelante.
  String _semanticLabel(BuildContext context, Strings s, FloorView v) {
    final parts = <String>[
      // El nombre propio ('Ventana 1') dice más que el número; si no tiene,
      // se cae al rótulo numerado que ya usa el resto de la app.
      table.name ?? s.tableLabel(table.number),
      s.floorState(v.status),
      if (v.minutes != null) s.minutesLabel(v.minutes!),
      if (v.totalAmount != null && v.currency != null)
        formatMoney(v.totalAmount!, v.currency!),
      if (v.waiterName != null) v.waiterName!,
    ];
    return parts.join('. ');
  }

  Color _accent(FloorStatus status, ColorScheme scheme) {
    switch (status) {
      case FloorStatus.toServe:
        return WellnodPalette.warnOn(scheme.brightness);
      case FloorStatus.toCharge:
        return WellnodPalette.warnOn(scheme.brightness);
      case FloorStatus.served:
        return WellnodPalette.successOn(scheme.brightness);
      case FloorStatus.inKitchen:
        return scheme.primary;
      case FloorStatus.open:
        return scheme.onSurfaceVariant;
      case FloorStatus.free:
      case FloorStatus.closed:
        return scheme.onSurfaceVariant;
    }
  }
}
