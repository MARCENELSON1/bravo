import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../api/api_error.dart';
import '../../l10n/strings.dart';
import '../../ui/glass_panel.dart';
import 'integrations_repository.dart';

/// Ajustes › Integraciones — paridad con el IntegrationsPanel del web para
/// Mercado Pago (OAuth connect + estado + desconectar). El resto de las
/// integraciones siguen como "Próximamente".
class IntegracionesSettingsSection extends ConsumerWidget {
  const IntegracionesSettingsSection({super.key});

  Future<void> _connect(BuildContext context, WidgetRef ref) async {
    final s = context.s;
    try {
      final url = await ref.read(integrationsRepositoryProvider).connectUrl();
      final uri = Uri.tryParse(url);
      final ok = uri != null &&
          await launchUrl(uri, mode: LaunchMode.externalApplication);
      if (!ok && context.mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(s.mpOpenError)));
      }
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
            content: Text(e is ApiError ? e.message : s.mpOpenError)));
      }
    }
  }

  Future<void> _disconnect(BuildContext context, WidgetRef ref) async {
    final s = context.s;
    try {
      await ref.read(integrationsRepositoryProvider).disconnectMercadoPago();
      ref.invalidate(mercadoPagoConnectionProvider);
      if (context.mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(s.mpDisconnected)));
      }
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
            content: Text(e is ApiError ? e.message : s.mpError)));
      }
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = context.s;
    final scheme = Theme.of(context).colorScheme;
    final async = ref.watch(mercadoPagoConnectionProvider);
    return GlassPanel(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(s.mpTitle,
                    style: Theme.of(context).textTheme.titleSmall),
              ),
              async.maybeWhen(
                data: (c) => _StatusChip(connected: c.connected),
                orElse: () => const SizedBox.shrink(),
              ),
            ],
          ),
          const SizedBox(height: 4),
          Text(s.mpDesc,
              style: TextStyle(color: scheme.onSurfaceVariant, fontSize: 13)),
          const SizedBox(height: 12),
          async.when(
            loading: () => const Padding(
              padding: EdgeInsets.all(8),
              child: Center(child: CircularProgressIndicator()),
            ),
            error: (e, _) => Text(e is ApiError ? e.message : s.mpError),
            data: (c) {
              if (c.connected) {
                return Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    if (c.nickname != null)
                      Text(c.nickname!,
                          style: const TextStyle(fontWeight: FontWeight.w500)),
                    Text(c.liveMode ? s.mpLiveMode : s.mpTestMode,
                        style: TextStyle(
                            color: scheme.onSurfaceVariant, fontSize: 13)),
                    const SizedBox(height: 12),
                    OutlinedButton(
                      onPressed: () => _disconnect(context, ref),
                      child: Text(s.mpDisconnect),
                    ),
                  ],
                );
              }
              return Align(
                alignment: Alignment.centerLeft,
                child: FilledButton(
                  onPressed: () => _connect(context, ref),
                  child: Text(s.mpConnect),
                ),
              );
            },
          ),
        ],
      ),
    );
  }
}

class _StatusChip extends StatelessWidget {
  const _StatusChip({required this.connected});
  final bool connected;
  @override
  Widget build(BuildContext context) {
    final s = context.s;
    final scheme = Theme.of(context).colorScheme;
    final color = connected ? scheme.primary : scheme.onSurfaceVariant;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(999),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(connected ? Icons.check_circle : Icons.circle_outlined,
              size: 14, color: color),
          const SizedBox(width: 4),
          Text(connected ? s.mpConnected : s.mpNotConnected,
              style: TextStyle(color: color, fontSize: 12)),
        ],
      ),
    );
  }
}
