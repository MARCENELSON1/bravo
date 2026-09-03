import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/api_error.dart';
import '../../l10n/strings.dart';
import '../../ui/glass_panel.dart';
import 'fiscal_repository.dart';

/// Ajustes › Datos del local — paridad con el FiscalAddressCard del web:
/// país/moneda/régimen de solo lectura + dirección fiscal editable.
class NegocioSettingsSection extends ConsumerWidget {
  const NegocioSettingsSection({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = context.s;
    final async = ref.watch(fiscalSettingsProvider);
    return GlassPanel(
      child: async.when(
        loading: () => const Padding(
          padding: EdgeInsets.all(8),
          child: Center(child: CircularProgressIndicator()),
        ),
        error: (e, _) => Text(e is ApiError ? e.message : s.fiscalError),
        data: (data) => _FiscalForm(initial: data),
      ),
    );
  }
}

class _FiscalForm extends ConsumerStatefulWidget {
  const _FiscalForm({required this.initial});
  final FiscalSettings initial;
  @override
  ConsumerState<_FiscalForm> createState() => _FiscalFormState();
}

class _FiscalFormState extends ConsumerState<_FiscalForm> {
  late final TextEditingController _street;
  late final TextEditingController _city;
  late final TextEditingController _state;
  late final TextEditingController _zip;
  bool _saving = false;

  @override
  void initState() {
    super.initState();
    _street = TextEditingController(text: widget.initial.street ?? '');
    _city = TextEditingController(text: widget.initial.city ?? '');
    _state = TextEditingController(text: widget.initial.state ?? '');
    _zip = TextEditingController(text: widget.initial.zip ?? '');
  }

  @override
  void dispose() {
    _street.dispose();
    _city.dispose();
    _state.dispose();
    _zip.dispose();
    super.dispose();
  }

  String? _nn(String v) => v.trim().isEmpty ? null : v.trim();

  Future<void> _save() async {
    final s = context.s;
    setState(() => _saving = true);
    try {
      await ref.read(fiscalRepositoryProvider).updateAddress(
            street: _nn(_street.text),
            city: _nn(_city.text),
            state: _nn(_state.text),
            zip: _nn(_zip.text),
          );
      ref.invalidate(fiscalSettingsProvider);
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(s.fiscalSaved)));
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
            content: Text(e is ApiError ? e.message : s.fiscalError)));
      }
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final s = context.s;
    final scheme = Theme.of(context).colorScheme;
    final d = widget.initial;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(s.fiscalTitle, style: Theme.of(context).textTheme.titleSmall),
        const SizedBox(height: 8),
        _readonly(context, s.fiscalCountry, d.country),
        _readonly(context, s.fiscalCurrency, d.currency),
        _readonly(context, s.fiscalRegime, d.taxRegime),
        Divider(height: 24, color: scheme.outlineVariant),
        TextField(
          controller: _street,
          decoration: InputDecoration(labelText: s.fiscalStreet),
        ),
        const SizedBox(height: 12),
        TextField(
          controller: _city,
          decoration: InputDecoration(labelText: s.fiscalCity),
        ),
        const SizedBox(height: 12),
        Row(
          children: [
            Expanded(
              child: TextField(
                controller: _state,
                decoration: InputDecoration(labelText: s.fiscalState),
              ),
            ),
            const SizedBox(width: 12),
            SizedBox(
              width: 120,
              child: TextField(
                controller: _zip,
                decoration: InputDecoration(labelText: s.fiscalZip),
              ),
            ),
          ],
        ),
        const SizedBox(height: 16),
        Align(
          alignment: Alignment.centerLeft,
          child: FilledButton(
            onPressed: _saving ? null : _save,
            child: Text(s.fiscalSave),
          ),
        ),
      ],
    );
  }

  Widget _readonly(BuildContext context, String label, String value) {
    final scheme = Theme.of(context).colorScheme;
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: TextStyle(color: scheme.onSurfaceVariant)),
          Text(value.isEmpty ? '—' : value,
              style: const TextStyle(fontWeight: FontWeight.w500)),
        ],
      ),
    );
  }
}
