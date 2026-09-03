import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/api_error.dart';
import '../../l10n/strings.dart';
import '../../ui/app_background.dart';
import '../../ui/glass_panel.dart';
import '../../ui/state_views.dart';
import '../../util/money.dart';
import '../cashier/payment_dtos.dart';
import 'expenses_repository.dart';

/// Gastos (paridad con `/app/expenses` del web): lista de egresos + alta rápida
/// (medio, monto, categoría, proveedor, descripción). Admin/cajero.
class GastosPage extends ConsumerWidget {
  const GastosPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = context.s;
    final async = ref.watch(expensesProvider);
    return Scaffold(
      backgroundColor: Colors.transparent,
      appBar: AppBar(
          title: Text(s.gastosTitle), backgroundColor: Colors.transparent),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _openForm(context, ref),
        icon: const Icon(Icons.add),
        label: Text(s.gastosNew),
      ),
      body: Stack(
        children: [
          const AppBackground(),
          SafeArea(
            child: async.when(
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (e, _) => ErrorView(
                  error: e, onRetry: () => ref.invalidate(expensesProvider)),
              data: (items) {
                Future<void> refresh() async =>
                    ref.invalidate(expensesProvider);
                if (items.isEmpty) {
                  return RefreshIndicator(
                    onRefresh: refresh,
                    child: ListView(
                      physics: const AlwaysScrollableScrollPhysics(),
                      children: [
                        SizedBox(
                            height: 280,
                            child: EmptyView(
                                message: s.gastosEmpty,
                                icon: Icons.receipt_long_outlined)),
                      ],
                    ),
                  );
                }
                return RefreshIndicator(
                  onRefresh: refresh,
                  child: ListView(
                    physics: const AlwaysScrollableScrollPhysics(),
                    padding: const EdgeInsets.fromLTRB(16, 16, 16, 96),
                    children: [
                      GlassPanel(
                        padding: const EdgeInsets.symmetric(vertical: 4),
                        child: Material(
                          type: MaterialType.transparency,
                          child: Column(
                            children: [
                              for (var i = 0; i < items.length; i++) ...[
                                if (i > 0) const Divider(height: 1),
                                _tile(context, s, items[i]),
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

  Widget _tile(BuildContext context, Strings s, Expense e) {
    final scheme = Theme.of(context).colorScheme;
    final title = e.counterparty ?? e.description ?? e.category ?? '—';
    final subParts = <String>[
      if (e.category != null) e.category!,
      if (e.counterparty != null && e.description != null) e.description!,
    ];
    return ListTile(
      title: Row(
        children: [
          Expanded(child: Text(title)),
          const SizedBox(width: 8),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
            decoration: BoxDecoration(
              color: scheme.surfaceContainerHighest,
              borderRadius: BorderRadius.circular(999),
            ),
            child: Text(s.methodLabel(PaymentMethod.fromApi(e.method)),
                style: const TextStyle(fontSize: 11)),
          ),
        ],
      ),
      subtitle: subParts.isEmpty ? null : Text(subParts.join(' · ')),
      trailing: Text('−${formatMoney(e.amount, e.currency)}',
          style: TextStyle(
              fontWeight: FontWeight.w600, color: scheme.error)),
    );
  }

  void _openForm(BuildContext context, WidgetRef ref) {
    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (_) => const _ExpenseForm(),
    );
  }
}

class _ExpenseForm extends ConsumerStatefulWidget {
  const _ExpenseForm();
  @override
  ConsumerState<_ExpenseForm> createState() => _ExpenseFormState();
}

class _ExpenseFormState extends ConsumerState<_ExpenseForm> {
  final _amount = TextEditingController();
  final _category = TextEditingController();
  final _counterparty = TextEditingController();
  final _description = TextEditingController();
  PaymentMethod _method = PaymentMethod.cash;
  bool _saving = false;

  static const _methods = [
    PaymentMethod.cash,
    PaymentMethod.transfer,
    PaymentMethod.card,
    PaymentMethod.mercadopago,
  ];

  @override
  void dispose() {
    _amount.dispose();
    _category.dispose();
    _counterparty.dispose();
    _description.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final s = context.s;
    final minor = pesosToMinor(_amount.text);
    if (minor == null || minor < 1) {
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text(s.gastosInvalidAmount)));
      return;
    }
    setState(() => _saving = true);
    try {
      await ref.read(expensesRepositoryProvider).register(
            method: _method.api,
            amount: minor,
            category: _nn(_category.text),
            counterparty: _nn(_counterparty.text),
            description: _nn(_description.text),
          );
      ref.invalidate(expensesProvider);
      if (mounted) {
        Navigator.of(context).pop();
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(s.gastosSaved)));
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
            content: Text(e is ApiError ? e.message : s.gastosError)));
      }
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  String? _nn(String v) => v.trim().isEmpty ? null : v.trim();

  @override
  Widget build(BuildContext context) {
    final s = context.s;
    return Padding(
      padding: EdgeInsets.only(
          bottom: MediaQuery.of(context).viewInsets.bottom + 16,
          left: 16,
          right: 16,
          top: 8),
      child: GlassPanel(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Center(
              child: Container(
                width: 40,
                height: 4,
                margin: const EdgeInsets.only(bottom: 12),
                decoration: BoxDecoration(
                    color: Theme.of(context).colorScheme.outlineVariant,
                    borderRadius: BorderRadius.circular(2)),
              ),
            ),
            Text(s.gastosNew, style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: DropdownButtonFormField<PaymentMethod>(
                    initialValue: _method,
                    decoration: InputDecoration(labelText: s.gastosMethod),
                    items: [
                      for (final m in _methods)
                        DropdownMenuItem(
                            value: m, child: Text(s.methodLabel(m))),
                    ],
                    onChanged: (m) => setState(() => _method = m ?? _method),
                  ),
                ),
                const SizedBox(width: 12),
                SizedBox(
                  width: 120,
                  child: TextField(
                    controller: _amount,
                    keyboardType:
                        const TextInputType.numberWithOptions(decimal: true),
                    decoration: InputDecoration(
                        labelText: s.gastosAmount, prefixText: r'$ '),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _category,
              decoration: InputDecoration(labelText: s.gastosCategory),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _counterparty,
              decoration: InputDecoration(labelText: s.gastosCounterparty),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _description,
              decoration: InputDecoration(labelText: s.gastosDescription),
            ),
            const SizedBox(height: 16),
            FilledButton.icon(
              onPressed: _saving ? null : _submit,
              icon: const Icon(Icons.check),
              label: Text(s.gastosNew),
            ),
          ],
        ),
      ),
    );
  }
}
