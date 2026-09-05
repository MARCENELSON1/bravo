import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../l10n/strings.dart';
import '../../util/money.dart';
import 'capture_logic.dart';
import 'product_dtos.dart';

typedef ItemOptions = ({int qty, String? note, List<String> optionIds});

/// "Cómo se quiere el plato": modificadores estructurados (chips por grupo,
/// con regla min/max y delta de precio) + cantidad + nota.
///
/// Dos modos, una sola pantalla:
/// - **quick** (tap en un producto con grupo obligatorio, ej. punto del bife):
///   solo los grupos obligatorios, cantidad 1. Si es un único grupo de
///   elegir-uno, tocar el chip **agrega al instante** (un toque, como prometía
///   la grilla). Con varios grupos, se confirma con "Agregar".
/// - **full** (mantener presionado): todos los grupos + cantidad + nota +
///   "Agregar ×N". "Agregar" queda deshabilitado hasta que la selección cumpla
///   la regla de cada grupo (espeja la validación del server).
Future<ItemOptions?> showItemOptionsSheet(
  BuildContext context,
  Product product, {
  required bool quick,
}) {
  return showModalBottomSheet<ItemOptions>(
    context: context,
    isScrollControlled: true,
    showDragHandle: true,
    builder: (_) => _ItemOptionsSheet(product: product, quick: quick),
  );
}

class _ItemOptionsSheet extends StatefulWidget {
  const _ItemOptionsSheet({required this.product, required this.quick});

  final Product product;
  final bool quick;

  @override
  State<_ItemOptionsSheet> createState() => _ItemOptionsSheetState();
}

class _ItemOptionsSheetState extends State<_ItemOptionsSheet> {
  int _qty = 1;
  final _note = TextEditingController();
  final _selected = <String>{};

  Product get _p => widget.product;

  /// En modo rápido solo mostramos lo obligatorio; en completo, todo.
  List<ModifierGroup> get _groups => widget.quick
      ? _p.modifierGroups.where((g) => g.required).toList()
      : _p.modifierGroups;

  /// Único grupo obligatorio de elegir-uno → el chip agrega solo (1 toque).
  bool get _autoConfirm =>
      widget.quick && _groups.length == 1 && _groups.single.single;

  bool get _valid => selectionValid(_p, _selected.toList());

  @override
  void dispose() {
    _note.dispose();
    super.dispose();
  }

  void _setQty(int q) {
    HapticFeedback.selectionClick();
    setState(() => _qty = q.clamp(1, 99));
  }

  void _toggle(ModifierGroup g, ModifierOption o) {
    HapticFeedback.selectionClick();
    setState(() {
      if (g.single) {
        // Elegir-uno: reemplaza la opción del grupo.
        _selected.removeWhere((id) => g.options.any((x) => x.id == id));
        _selected.add(o.id);
      } else if (_selected.contains(o.id)) {
        _selected.remove(o.id);
      } else if (g.options.where((x) => _selected.contains(x.id)).length <
          g.maxSelect) {
        _selected.add(o.id);
      }
    });
    if (_autoConfirm && _valid) _confirm();
  }

  void _confirm() {
    final note = _note.text.trim();
    Navigator.of(context).pop((
      qty: _qty,
      note: note.isEmpty ? null : note,
      optionIds: _selected.toList(),
    ));
  }

  @override
  Widget build(BuildContext context) {
    final s = context.s;
    final theme = Theme.of(context);
    final delta = optionsDelta(_p, _selected.toList());
    final unit = _p.priceAmount + delta;

    return Padding(
      padding: EdgeInsets.fromLTRB(
        20,
        0,
        20,
        MediaQuery.of(context).viewInsets.bottom + 20,
      ),
      child: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(
              _p.name,
              style: theme.textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.w700,
              ),
            ),
            Text(
              formatMoney(unit, _p.currency),
              style: TextStyle(color: theme.colorScheme.onSurfaceVariant),
            ),
            for (final g in _groups) _group(context, s, g),
            if (!widget.quick) ...[
              const SizedBox(height: 14),
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  IconButton.outlined(
                    iconSize: 28,
                    icon: const Icon(Icons.remove),
                    onPressed: _qty > 1 ? () => _setQty(_qty - 1) : null,
                  ),
                  SizedBox(
                    width: 80,
                    child: Text(
                      '$_qty',
                      textAlign: TextAlign.center,
                      style: theme.textTheme.displaySmall?.copyWith(
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ),
                  IconButton.filled(
                    iconSize: 28,
                    icon: const Icon(Icons.add),
                    onPressed: () => _setQty(_qty + 1),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Wrap(
                spacing: 8,
                alignment: WrapAlignment.center,
                children: [
                  for (final n in const [2, 3, 4, 6])
                    ChoiceChip(
                      label: Text('×$n'),
                      selected: _qty == n,
                      onSelected: (_) => _setQty(n),
                    ),
                ],
              ),
              const SizedBox(height: 14),
              TextField(
                controller: _note,
                textCapitalization: TextCapitalization.sentences,
                decoration: InputDecoration(
                  hintText: s.captureNoteHint,
                  prefixIcon: const Icon(Icons.edit_note_outlined),
                ),
              ),
            ],
            // Con auto-confirm el chip ya agrega: no hace falta botón.
            if (!_autoConfirm) ...[
              const SizedBox(height: 16),
              FilledButton.icon(
                onPressed: _valid ? _confirm : null,
                icon: const Icon(Icons.add),
                label: Text(s.addQty(_qty)),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _group(BuildContext context, Strings s, ModifierGroup g) {
    final theme = Theme.of(context);
    final rule = g.required
        ? (g.single ? s.modPickOne : s.modAtLeast(g.minSelect))
        : s.modUpTo(g.maxSelect);
    return Padding(
      padding: const EdgeInsets.only(top: 14),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Text(
                g.name,
                style: theme.textTheme.titleSmall?.copyWith(
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(width: 8),
              Text(
                rule,
                style: theme.textTheme.labelSmall?.copyWith(
                  color: g.required
                      ? theme.colorScheme.primary
                      : theme.colorScheme.onSurfaceVariant,
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              for (final o in g.options)
                FilterChip(
                  label: Text(
                    o.priceDelta > 0
                        ? '${o.name} +${formatMoney(o.priceDelta, _p.currency)}'
                        : o.name,
                  ),
                  selected: _selected.contains(o.id),
                  showCheckmark: false,
                  onSelected: (_) => _toggle(g, o),
                ),
            ],
          ),
        ],
      ),
    );
  }
}
