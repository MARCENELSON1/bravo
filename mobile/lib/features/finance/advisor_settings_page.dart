import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/api_error.dart';
import '../../l10n/strings.dart';
import '../../ui/app_background.dart';
import '../../ui/glass_panel.dart';
import '../../util/money.dart';
import 'advisor_settings_repository.dart';

/// Config del asesor/finanzas (costos fijos, food cost objetivo, IVA, inflación,
/// cubiertos, horario). Vive en Finanzas (igual que en la web, no en Ajustes).
/// Los `%` se guardan como bps.
class AdvisorSettingsPage extends ConsumerStatefulWidget {
  const AdvisorSettingsPage({super.key});

  @override
  ConsumerState<AdvisorSettingsPage> createState() => _AdvisorSettingsPageState();
}

class _AdvisorSettingsPageState extends ConsumerState<AdvisorSettingsPage> {
  final _labor = TextEditingController();
  final _other = TextEditingController();
  final _foodCost = TextEditingController();
  final _vat = TextEditingController();
  final _inflation = TextEditingController();
  final _seats = TextEditingController();
  final _minutes = TextEditingController();
  bool _filled = false;

  @override
  void dispose() {
    for (final c in [_labor, _other, _foodCost, _vat, _inflation, _seats, _minutes]) {
      c.dispose();
    }
    super.dispose();
  }

  void _fill(AdvisorSettings s) {
    _labor.text = (s.monthlyLaborCost / 100).toStringAsFixed(2);
    _other.text = (s.monthlyOtherFixedCosts / 100).toStringAsFixed(2);
    _foodCost.text = (s.targetFoodCostBps / 100).toStringAsFixed(2);
    _vat.text = (s.defaultVatBps / 100).toStringAsFixed(2);
    _inflation.text = (s.monthlyInflationBps / 100).toStringAsFixed(2);
    _seats.text = '${s.seats}';
    _minutes.text = '${s.dailyOpenMinutes}';
    _filled = true;
  }

  @override
  Widget build(BuildContext context) {
    final s = context.s;
    final async = ref.watch(advisorSettingsProvider);
    return Scaffold(
      backgroundColor: Colors.transparent,
      appBar: AppBar(
          title: Text(s.advisorConfigTitle),
          backgroundColor: Colors.transparent),
      body: Stack(
        children: [
          const AppBackground(),
          SafeArea(
            child: async.when(
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (e, _) => Center(
                child: Padding(
                  padding: const EdgeInsets.all(24),
                  child: Text(e is ApiError ? e.message : '$e'),
                ),
              ),
              data: (settings) {
                if (!_filled) _fill(settings);
                return _form(s);
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _form(Strings s) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        GlassPanel(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              _money(_labor, s.setLaborCost),
              _money(_other, s.setOtherFixed),
              _num(_foodCost, s.setTargetFoodCost),
              _num(_vat, s.setVat),
              _num(_inflation, s.setInflation),
              _int(_seats, s.setSeats),
              _int(_minutes, s.setOpenMinutes),
              const SizedBox(height: 16),
              FilledButton.icon(
                onPressed: _save,
                icon: const Icon(Icons.save_outlined),
                label: Text(s.setSave),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _money(TextEditingController c, String label) => Padding(
        padding: const EdgeInsets.only(bottom: 10),
        child: TextField(
          controller: c,
          keyboardType: const TextInputType.numberWithOptions(decimal: true),
          decoration: InputDecoration(labelText: label),
        ),
      );

  Widget _num(TextEditingController c, String label) => _money(c, label);

  Widget _int(TextEditingController c, String label) => Padding(
        padding: const EdgeInsets.only(bottom: 10),
        child: TextField(
          controller: c,
          keyboardType: TextInputType.number,
          decoration: InputDecoration(labelText: label),
        ),
      );

  int _pctToBps(TextEditingController c) {
    final v = double.tryParse(c.text.trim().replaceAll(',', '.')) ?? 0;
    return (v * 100).round();
  }

  Future<void> _save() async {
    final s = context.s;
    try {
      await ref.read(advisorSettingsRepositoryProvider).update(
            monthlyLaborCost: pesosToMinor(_labor.text) ?? 0,
            monthlyOtherFixedCosts: pesosToMinor(_other.text) ?? 0,
            targetFoodCostBps: _pctToBps(_foodCost),
            seats: int.tryParse(_seats.text.trim()) ?? 0,
            dailyOpenMinutes: int.tryParse(_minutes.text.trim()) ?? 0,
            monthlyInflationBps: _pctToBps(_inflation),
            defaultVatBps: _pctToBps(_vat),
          );
      ref.invalidate(advisorSettingsProvider);
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(s.setSaved)));
      }
    } on ApiError catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(e.message)));
      }
    }
  }
}
