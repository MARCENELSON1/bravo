import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../l10n/strings.dart';
import '../../util/money.dart';
import 'product_dtos.dart';

typedef QtyNote = ({int qty, String? note});

/// Mantener presionado un producto en la grilla: cantidad rápida (×2 ×3 ×4…)
/// + nota para cocina ("sin sal", "bien cocido"). Devuelve null si se cancela.
Future<QtyNote?> showQtyNoteSheet(BuildContext context, Product product) {
  return showModalBottomSheet<QtyNote>(
    context: context,
    isScrollControlled: true,
    showDragHandle: true,
    builder: (_) => _QtyNoteSheet(product: product),
  );
}

class _QtyNoteSheet extends StatefulWidget {
  const _QtyNoteSheet({required this.product});

  final Product product;

  @override
  State<_QtyNoteSheet> createState() => _QtyNoteSheetState();
}

class _QtyNoteSheetState extends State<_QtyNoteSheet> {
  int _qty = 1;
  final _note = TextEditingController();

  @override
  void dispose() {
    _note.dispose();
    super.dispose();
  }

  void _set(int q) {
    HapticFeedback.selectionClick();
    setState(() => _qty = q.clamp(1, 99));
  }

  @override
  Widget build(BuildContext context) {
    final s = context.s;
    final p = widget.product;
    final theme = Theme.of(context);
    return Padding(
      padding: EdgeInsets.fromLTRB(
          20, 0, 20, MediaQuery.of(context).viewInsets.bottom + 20),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(p.name,
              style: theme.textTheme.titleLarge
                  ?.copyWith(fontWeight: FontWeight.w700)),
          Text(formatMoney(p.priceAmount, p.currency),
              style: TextStyle(color: theme.colorScheme.onSurfaceVariant)),
          const SizedBox(height: 16),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              IconButton.outlined(
                iconSize: 28,
                icon: const Icon(Icons.remove),
                onPressed: _qty > 1 ? () => _set(_qty - 1) : null,
              ),
              SizedBox(
                width: 80,
                child: Text('$_qty',
                    textAlign: TextAlign.center,
                    style: theme.textTheme.displaySmall
                        ?.copyWith(fontWeight: FontWeight.w700)),
              ),
              IconButton.filled(
                iconSize: 28,
                icon: const Icon(Icons.add),
                onPressed: () => _set(_qty + 1),
              ),
            ],
          ),
          const SizedBox(height: 10),
          Wrap(
            spacing: 8,
            alignment: WrapAlignment.center,
            children: [
              for (final n in const [2, 3, 4, 6])
                ChoiceChip(
                  label: Text('×$n'),
                  selected: _qty == n,
                  onSelected: (_) => _set(n),
                ),
            ],
          ),
          const SizedBox(height: 16),
          TextField(
            controller: _note,
            textCapitalization: TextCapitalization.sentences,
            decoration: InputDecoration(
              hintText: s.captureNoteHint,
              prefixIcon: const Icon(Icons.edit_note_outlined),
            ),
          ),
          const SizedBox(height: 16),
          FilledButton.icon(
            onPressed: () {
              final note = _note.text.trim();
              Navigator.of(context)
                  .pop((qty: _qty, note: note.isEmpty ? null : note));
            },
            icon: const Icon(Icons.add),
            label: Text(s.addQty(_qty)),
          ),
        ],
      ),
    );
  }
}
