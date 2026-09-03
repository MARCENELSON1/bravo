import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:qr_flutter/qr_flutter.dart';

import '../../api/api_error.dart';
import '../../l10n/strings.dart';
import '../../ui/app_background.dart';
import '../../ui/glass_panel.dart';
import '../../ui/state_views.dart';
import 'table_qr_repository.dart';

/// Mesas QR (paridad con `/app/mesas-qr` del web): config de autopedido + pago
/// en mesa + un QR por mesa activa. Lado dueño (OWNER/MANAGER).
class MesasQrPage extends ConsumerWidget {
  const MesasQrPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = context.s;
    final async = ref.watch(tablesProvider);
    return Scaffold(
      backgroundColor: Colors.transparent,
      appBar: AppBar(
          title: Text(s.mesasQrTitle), backgroundColor: Colors.transparent),
      body: Stack(
        children: [
          const AppBackground(),
          SafeArea(
            child: RefreshIndicator(
              onRefresh: () async {
                ref.invalidate(tablesProvider);
                ref.invalidate(selfOrderSettingsProvider);
                ref.invalidate(selfPaySettingsProvider);
              },
              child: ListView(
                physics: const AlwaysScrollableScrollPhysics(),
                padding: const EdgeInsets.all(16),
                children: [
                  const _SelfOrderCard(),
                  const SizedBox(height: 12),
                  const _SelfPayCard(),
                  const SizedBox(height: 16),
                  async.when(
                    loading: () => const Padding(
                      padding: EdgeInsets.all(24),
                      child: Center(child: CircularProgressIndicator()),
                    ),
                    error: (e, _) => ErrorView(
                        error: e, onRetry: () => ref.invalidate(tablesProvider)),
                    data: (tables) {
                      final active = tables.where((t) => t.active).toList();
                      if (active.isEmpty) {
                        return SizedBox(
                            height: 160,
                            child: EmptyView(
                                message: s.mesasQrEmpty,
                                icon: Icons.qr_code_2_outlined));
                      }
                      return Wrap(
                        spacing: 12,
                        runSpacing: 12,
                        alignment: WrapAlignment.center,
                        children: [
                          for (final t in active) _QrCard(table: t),
                        ],
                      );
                    },
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _QrCard extends ConsumerWidget {
  const _QrCard({required this.table});
  final TableItem table;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = context.s;
    final scheme = Theme.of(context).colorScheme;
    final async = ref.watch(tableQrUrlProvider(table.id));
    return GlassPanel(
      blur: false,
      padding: const EdgeInsets.all(14),
      radius: 18,
      child: SizedBox(
        width: 150,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(s.mesasQrTableLabel(table.number),
                style: const TextStyle(fontWeight: FontWeight.w700)),
            const SizedBox(height: 8),
            async.when(
              loading: () => const SizedBox(
                  height: 148,
                  child: Center(child: CircularProgressIndicator())),
              error: (e, _) => SizedBox(
                height: 148,
                child: Center(
                  child: Text(s.mesasQrLoadError,
                      textAlign: TextAlign.center,
                      style: TextStyle(color: scheme.error, fontSize: 12)),
                ),
              ),
              data: (url) => Container(
                // Fondo blanco SIEMPRE (aunque el tema sea oscuro) para que escanee.
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(10),
                ),
                child: QrImageView(
                  data: url,
                  version: QrVersions.auto,
                  size: 116,
                ),
              ),
            ),
            const SizedBox(height: 6),
            Text(s.mesasQrScanHint,
                textAlign: TextAlign.center,
                style: TextStyle(color: scheme.onSurfaceVariant, fontSize: 11)),
          ],
        ),
      ),
    );
  }
}

class _SelfOrderCard extends ConsumerStatefulWidget {
  const _SelfOrderCard();
  @override
  ConsumerState<_SelfOrderCard> createState() => _SelfOrderCardState();
}

class _SelfOrderCardState extends ConsumerState<_SelfOrderCard> {
  bool _saving = false;

  Future<void> _saveMode(String mode) async {
    setState(() => _saving = true);
    try {
      await ref.read(tableQrRepositoryProvider).updateSelfOrderMode(mode);
      // Autoservicio necesita el pago en mesa → prenderlo si hace falta.
      if (mode == 'SELF_SERVICE') {
        final pay = ref.read(selfPaySettingsProvider).valueOrNull;
        if (pay == null || !pay.enabled) {
          await ref.read(tableQrRepositoryProvider).updateSelfPay(
                (pay ?? const SelfPaySettings(enabled: false, tipsEnabled: true))
                    .copyWith(enabled: true),
              );
          ref.invalidate(selfPaySettingsProvider);
        }
      }
      ref.invalidate(selfOrderSettingsProvider);
    } catch (e) {
      if (mounted) {
        final s = context.s;
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
            content: Text(e is ApiError ? e.message : s.settingsSaveError)));
      }
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final s = context.s;
    final async = ref.watch(selfOrderSettingsProvider);
    return GlassPanel(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(s.selfOrderTitle, style: Theme.of(context).textTheme.titleSmall),
          Text(s.selfOrderSubtitle,
              style: TextStyle(
                  color: Theme.of(context).colorScheme.onSurfaceVariant,
                  fontSize: 13)),
          async.when(
            loading: () => const Padding(
                padding: EdgeInsets.all(8),
                child: Center(child: CircularProgressIndicator())),
            error: (e, _) => Text(e is ApiError ? e.message : s.settingsSaveError),
            data: (v) => Column(
              children: [
                for (final mode in const ['READ_ONLY', 'SALON', 'SELF_SERVICE'])
                  ListTile(
                    contentPadding: EdgeInsets.zero,
                    leading: Icon(
                      v.mode == mode
                          ? Icons.radio_button_checked
                          : Icons.radio_button_unchecked,
                      color: v.mode == mode
                          ? Theme.of(context).colorScheme.primary
                          : Theme.of(context).colorScheme.onSurfaceVariant,
                    ),
                    title: Text(s.selfOrderMode(mode)),
                    subtitle: Text(s.selfOrderModeHint(mode)),
                    onTap:
                        (_saving || v.mode == mode) ? null : () => _saveMode(mode),
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _SelfPayCard extends ConsumerStatefulWidget {
  const _SelfPayCard();
  @override
  ConsumerState<_SelfPayCard> createState() => _SelfPayCardState();
}

class _SelfPayCardState extends ConsumerState<_SelfPayCard> {
  bool _saving = false;

  Future<void> _save(SelfPaySettings next) async {
    setState(() => _saving = true);
    try {
      await ref.read(tableQrRepositoryProvider).updateSelfPay(next);
      ref.invalidate(selfPaySettingsProvider);
    } catch (e) {
      if (mounted) {
        final s = context.s;
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
            content: Text(e is ApiError ? e.message : s.settingsSaveError)));
      }
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final s = context.s;
    final async = ref.watch(selfPaySettingsProvider);
    return GlassPanel(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(s.selfPayTitle, style: Theme.of(context).textTheme.titleSmall),
          Text(s.selfPaySubtitle,
              style: TextStyle(
                  color: Theme.of(context).colorScheme.onSurfaceVariant,
                  fontSize: 13)),
          async.when(
            loading: () => const Padding(
                padding: EdgeInsets.all(8),
                child: Center(child: CircularProgressIndicator())),
            error: (e, _) => Text(e is ApiError ? e.message : s.settingsSaveError),
            data: (v) => Column(
              children: [
                SwitchListTile(
                  contentPadding: EdgeInsets.zero,
                  value: v.enabled,
                  onChanged:
                      _saving ? null : (x) => _save(v.copyWith(enabled: x)),
                  title: Text(s.selfPayEnable),
                  subtitle: Text(s.selfPayEnableHint),
                ),
                SwitchListTile(
                  contentPadding: EdgeInsets.zero,
                  value: v.tipsEnabled,
                  onChanged: (_saving || !v.enabled)
                      ? null
                      : (x) => _save(v.copyWith(tipsEnabled: x)),
                  title: Text(s.selfPayOfferTip),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
