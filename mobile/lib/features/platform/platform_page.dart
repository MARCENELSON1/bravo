import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/api_error.dart';
import '../../l10n/strings.dart';
import '../../ui/app_background.dart';
import '../../ui/glass_panel.dart';
import '../../ui/state_views.dart';
import '../../util/money.dart';
import 'platform_repository.dart';

const _currencyByRegion = {'AR': 'ARS', 'INTL': 'USD'};

/// Panel de Plataforma (paridad con `/app/platform` del web): super-admin del
/// catálogo global de planes. Gateado por `GET /platform/access` (platform_admin).
class PlatformPage extends ConsumerWidget {
  const PlatformPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = context.s;
    final plans = ref.watch(platformPlansProvider);
    return Scaffold(
      backgroundColor: Colors.transparent,
      appBar: AppBar(
          title: Text(s.platformTitle), backgroundColor: Colors.transparent),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _openForm(context, ref, null),
        icon: const Icon(Icons.add),
        label: Text(s.platformNewPlan),
      ),
      body: Stack(
        children: [
          const AppBackground(),
          SafeArea(
            child: plans.when(
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (e, _) => ErrorView(
                  error: e, onRetry: () => ref.invalidate(platformPlansProvider)),
              data: (list) {
                Future<void> refresh() async =>
                    ref.invalidate(platformPlansProvider);
                if (list.isEmpty) {
                  return RefreshIndicator(
                    onRefresh: refresh,
                    child: ListView(
                      physics: const AlwaysScrollableScrollPhysics(),
                      children: [
                        SizedBox(
                            height: 280,
                            child: EmptyView(
                                message: s.platformEmpty,
                                icon: Icons.workspace_premium_outlined)),
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
                      Text(s.platformCatalog,
                          style: Theme.of(context).textTheme.titleSmall),
                      const SizedBox(height: 8),
                      for (final p in list) _planTile(context, ref, s, p),
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

  Widget _planTile(
      BuildContext context, WidgetRef ref, Strings s, PlatformPlan p) {
    final scheme = Theme.of(context).colorScheme;
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: GlassPanel(
        blur: false,
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                    width: 8,
                    height: 8,
                    decoration: BoxDecoration(
                        color: p.active
                            ? scheme.primary
                            : scheme.onSurfaceVariant.withValues(alpha: 0.4),
                        shape: BoxShape.circle)),
                const SizedBox(width: 8),
                Text('${p.tier} · ${s.platformRegionLabel(p.region)}',
                    style: const TextStyle(fontWeight: FontWeight.w700)),
                const Spacer(),
                Text(
                    '${formatMoney(p.amount, p.currency)} / ${s.billingInterval(p.interval)}',
                    style: TextStyle(color: scheme.onSurfaceVariant)),
              ],
            ),
            const SizedBox(height: 2),
            Row(
              children: [
                Expanded(
                  child: Text('${p.features.length} ${s.platformIncludes.toLowerCase()}',
                      style: TextStyle(
                          color: scheme.onSurfaceVariant, fontSize: 12)),
                ),
                TextButton(
                  onPressed: () => _openForm(context, ref, p),
                  child: Text(s.setEdit),
                ),
                TextButton(
                  onPressed: () => _delete(context, ref, s, p),
                  style: TextButton.styleFrom(foregroundColor: scheme.error),
                  child: Text(s.setDelete),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _delete(
      BuildContext context, WidgetRef ref, Strings s, PlatformPlan p) async {
    final ok = await confirmDialog(context,
        title: s.platformDeleteConfirm, confirmLabel: s.setDelete);
    if (!ok) return;
    try {
      await ref.read(platformRepositoryProvider).deletePlan(p.id);
      ref.invalidate(platformPlansProvider);
      if (context.mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(s.platformDeleted)));
      }
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
            content: Text(e is ApiError ? e.message : s.platformDeleteError)));
      }
    }
  }

  void _openForm(BuildContext context, WidgetRef ref, PlatformPlan? plan) {
    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (_) => _PlanForm(plan: plan),
    );
  }
}

class _PlanForm extends ConsumerStatefulWidget {
  const _PlanForm({required this.plan});
  final PlatformPlan? plan;
  @override
  ConsumerState<_PlanForm> createState() => _PlanFormState();
}

class _PlanFormState extends ConsumerState<_PlanForm> {
  late String _tier = widget.plan?.tier ?? 'PRO';
  late String _region = widget.plan?.region ?? 'INTL';
  late String _interval = widget.plan?.interval ?? 'MONTH';
  late final _amount = TextEditingController(
      text: widget.plan != null
          ? (widget.plan!.amount / 100).toStringAsFixed(2)
          : '');
  late bool _active = widget.plan?.active ?? true;
  late final Set<String> _selected = {...?widget.plan?.features};
  bool _saving = false;

  @override
  void dispose() {
    _amount.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final s = context.s;
    final minor = pesosToMinor(_amount.text);
    if (minor == null || minor < 0) {
      _snack(s.platformInvalidPrice);
      return;
    }
    setState(() => _saving = true);
    try {
      await ref.read(platformRepositoryProvider).savePlan(
            id: widget.plan?.id,
            tier: _tier,
            region: _region,
            amount: minor,
            currency: _currencyByRegion[_region] ?? 'USD',
            interval: _interval,
            features: _selected.toList(),
            active: _active,
          );
      ref.invalidate(platformPlansProvider);
      if (mounted) {
        Navigator.of(context).pop();
        _snack(s.platformSaved);
      }
    } catch (e) {
      if (mounted) _snack(e is ApiError ? e.message : s.platformSaveError);
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  void _snack(String m) =>
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(m)));

  @override
  Widget build(BuildContext context) {
    final s = context.s;
    final features = ref.watch(platformFeaturesProvider);
    final currency = _currencyByRegion[_region] ?? 'USD';
    return Padding(
      padding: EdgeInsets.only(
          bottom: MediaQuery.of(context).viewInsets.bottom + 16,
          left: 16,
          right: 16,
          top: 8),
      child: GlassPanel(
        child: SingleChildScrollView(
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
              Text(widget.plan == null ? s.platformNewPlan : s.platformEditPlan,
                  style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: 12),
              Row(
                children: [
                  Expanded(
                    child: DropdownButtonFormField<String>(
                      initialValue: _tier,
                      decoration: InputDecoration(labelText: s.platformTier),
                      items: const [
                        DropdownMenuItem(value: 'BASIC', child: Text('BASIC')),
                        DropdownMenuItem(value: 'PRO', child: Text('PRO')),
                        DropdownMenuItem(
                            value: 'ENTERPRISE', child: Text('ENTERPRISE')),
                      ],
                      onChanged: (v) => setState(() => _tier = v ?? _tier),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: DropdownButtonFormField<String>(
                      initialValue: _region,
                      decoration: InputDecoration(labelText: s.platformRegion),
                      items: [
                        for (final r in ['AR', 'INTL'])
                          DropdownMenuItem(
                              value: r, child: Text(s.platformRegionLabel(r))),
                      ],
                      onChanged: (v) => setState(() => _region = v ?? _region),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _amount,
                      keyboardType:
                          const TextInputType.numberWithOptions(decimal: true),
                      decoration:
                          InputDecoration(labelText: s.platformPrice(currency)),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: DropdownButtonFormField<String>(
                      initialValue: _interval,
                      decoration:
                          InputDecoration(labelText: s.platformIntervalLabel),
                      items: [
                        for (final i in ['MONTH', 'YEAR'])
                          DropdownMenuItem(
                              value: i, child: Text(s.billingInterval(i))),
                      ],
                      onChanged: (v) => setState(() => _interval = v ?? _interval),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              Text(s.platformIncludes,
                  style: const TextStyle(fontWeight: FontWeight.w600)),
              features.maybeWhen(
                data: (list) => Column(
                  children: [
                    for (final f in list)
                      CheckboxListTile(
                        contentPadding: EdgeInsets.zero,
                        dense: true,
                        value: _selected.contains(f.key),
                        onChanged: (v) => setState(() {
                          if (v == true) {
                            _selected.add(f.key);
                          } else {
                            _selected.remove(f.key);
                          }
                        }),
                        title: Text(f.label),
                      ),
                  ],
                ),
                orElse: () => const Padding(
                  padding: EdgeInsets.all(8),
                  child: Center(child: CircularProgressIndicator()),
                ),
              ),
              SwitchListTile(
                contentPadding: EdgeInsets.zero,
                value: _active,
                onChanged: (v) => setState(() => _active = v),
                title: Text(s.platformActive),
              ),
              const SizedBox(height: 12),
              FilledButton.icon(
                onPressed: _saving ? null : _submit,
                icon: const Icon(Icons.check),
                label: Text(widget.plan == null
                    ? s.platformCreate
                    : s.platformSaveChanges),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
