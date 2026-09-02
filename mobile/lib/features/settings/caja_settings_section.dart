import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/api_error.dart';
import '../../l10n/strings.dart';
import '../../ui/glass_panel.dart';
import 'cash_settings_repository.dart';

/// Ajustes › Caja y pagos — paridad con la web: política de caja (2 toggles) +
/// comisiones por medio de pago. Editable por OWNER/MANAGER.
class CajaSettingsSection extends ConsumerWidget {
  const CajaSettingsSection({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return const Column(
      children: [
        _CashPolicyCard(),
        SizedBox(height: 16),
        _CommissionsCard(),
      ],
    );
  }
}

class _CashPolicyCard extends ConsumerStatefulWidget {
  const _CashPolicyCard();
  @override
  ConsumerState<_CashPolicyCard> createState() => _CashPolicyCardState();
}

class _CashPolicyCardState extends ConsumerState<_CashPolicyCard> {
  bool _saving = false;

  Future<void> _set(CashSettings base, CashSettings next) async {
    setState(() => _saving = true);
    try {
      await ref.read(cashSettingsRepositoryProvider).updateSettings(next);
      ref.invalidate(cashSettingsProvider);
    } catch (e) {
      if (mounted) {
        final s = context.s;
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
            content: Text(e is ApiError ? e.message : s.cashSaveError)));
      }
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final s = context.s;
    final async = ref.watch(cashSettingsProvider);
    return GlassPanel(
      child: async.when(
        loading: () => const Padding(
          padding: EdgeInsets.all(8),
          child: Center(child: CircularProgressIndicator()),
        ),
        error: (e, _) => Text(e is ApiError ? e.message : s.cashSaveError),
        data: (data) => Column(
          children: [
            SwitchListTile(
              contentPadding: EdgeInsets.zero,
              value: data.requireOpenCashSession,
              onChanged: _saving
                  ? null
                  : (v) => _set(data,
                      data.copyWith(requireOpenCashSession: v)),
              title: Text(s.cashRequireOpenTitle),
              subtitle: Text(s.cashRequireOpenDesc),
            ),
            const Divider(height: 1),
            SwitchListTile(
              contentPadding: EdgeInsets.zero,
              value: data.blindCashCount,
              onChanged: _saving
                  ? null
                  : (v) => _set(data, data.copyWith(blindCashCount: v)),
              title: Text(s.cashBlindTitle),
              subtitle: Text(s.cashBlindDesc),
            ),
          ],
        ),
      ),
    );
  }
}

const _commissionMethods = ['CARD', 'MERCADOPAGO', 'QR'];

class _CommissionsCard extends ConsumerWidget {
  const _CommissionsCard();
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = context.s;
    final async = ref.watch(feeRatesProvider);
    return GlassPanel(
      child: async.when(
        loading: () => const Padding(
          padding: EdgeInsets.all(8),
          child: Center(child: CircularProgressIndicator()),
        ),
        error: (e, _) =>
            Text(e is ApiError ? e.message : s.commissionsSaveError),
        data: (rates) => _CommissionsForm(initial: rates),
      ),
    );
  }
}

class _CommissionsForm extends ConsumerStatefulWidget {
  const _CommissionsForm({required this.initial});
  final List<FeeRate> initial;
  @override
  ConsumerState<_CommissionsForm> createState() => _CommissionsFormState();
}

class _CommissionsFormState extends ConsumerState<_CommissionsForm> {
  late final Map<String, TextEditingController> _controllers;
  bool _saving = false;

  @override
  void initState() {
    super.initState();
    _controllers = {
      for (final m in _commissionMethods)
        m: TextEditingController(text: _initialText(m)),
    };
  }

  String _initialText(String method) {
    FeeRate? r;
    for (final x in widget.initial) {
      if (x.method == method) {
        r = x;
        break;
      }
    }
    if (r == null || r.feeBps == 0) return '';
    final pct = r.feeBps / 100;
    return pct == pct.roundToDouble()
        ? pct.toStringAsFixed(0)
        : pct.toString();
  }

  @override
  void dispose() {
    for (final c in _controllers.values) {
      c.dispose();
    }
    super.dispose();
  }

  Future<void> _save() async {
    final s = context.s;
    final payload = <FeeRate>[];
    for (final m in _commissionMethods) {
      final raw = _controllers[m]!.text.trim();
      final pct = raw.isEmpty ? 0.0 : double.tryParse(raw);
      if (pct == null || pct < 0 || pct > 100) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(s.commissionsInvalid)));
        return;
      }
      payload.add(FeeRate(method: m, feeBps: (pct * 100).round()));
    }
    setState(() => _saving = true);
    try {
      await ref.read(cashSettingsRepositoryProvider).updateFeeRates(payload);
      ref.invalidate(feeRatesProvider);
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(s.commissionsSaved)));
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
            content: Text(e is ApiError ? e.message : s.commissionsSaveError)));
      }
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final s = context.s;
    final scheme = Theme.of(context).colorScheme;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(s.commissionsTitle,
            style: Theme.of(context).textTheme.titleSmall),
        const SizedBox(height: 4),
        Text(s.commissionsDesc,
            style: TextStyle(color: scheme.onSurfaceVariant, fontSize: 13)),
        const SizedBox(height: 12),
        for (final m in _commissionMethods)
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 4),
            child: Row(
              children: [
                Expanded(child: Text(s.payMethodLabel(m))),
                SizedBox(
                  width: 96,
                  child: TextField(
                    controller: _controllers[m],
                    keyboardType:
                        const TextInputType.numberWithOptions(decimal: true),
                    textAlign: TextAlign.right,
                    decoration: const InputDecoration(
                      hintText: '0',
                      suffixText: '%',
                      isDense: true,
                    ),
                  ),
                ),
              ],
            ),
          ),
        const SizedBox(height: 12),
        Align(
          alignment: Alignment.centerLeft,
          child: FilledButton(
            onPressed: _saving ? null : _save,
            child: Text(s.commissionsSave),
          ),
        ),
      ],
    );
  }
}
