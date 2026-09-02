import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import '../../api/api_error.dart';
import '../../l10n/strings.dart';
import '../../ui/app_background.dart';
import '../../ui/glass_panel.dart';
import 'timeclock_dtos.dart';
import 'timeclock_repository.dart';

/// Fichaje (Fase 4): fichar entrada/salida y ver turnos recientes.
class FichajePage extends ConsumerWidget {
  const FichajePage({super.key});

  static final _fmt = DateFormat('dd/MM HH:mm');

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = context.s;
    final async = ref.watch(myTimeclockProvider);

    return Scaffold(
      backgroundColor: Colors.transparent,
      appBar: AppBar(title: Text(s.fichajeTitle), backgroundColor: Colors.transparent),
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
              data: (tc) => _content(context, ref, s, tc),
            ),
          ),
        ],
      ),
    );
  }

  Widget _content(BuildContext context, WidgetRef ref, Strings s, MyTimeclock tc) {
    final open = tc.openShift;
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        GlassPanel(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              if (open != null) ...[
                Text(s.clockedInSince(_fmt.format(open.clockInAt)),
                    style: Theme.of(context).textTheme.titleMedium),
                const SizedBox(height: 4),
                Text(
                    '${s.workedTime}: ${s.durationLabel(DateTime.now().difference(open.clockInAt).inMinutes)}'),
                const SizedBox(height: 16),
                FilledButton.icon(
                  onPressed: () => _clockOut(context, ref),
                  icon: const Icon(Icons.logout),
                  label: Text(s.clockOut),
                ),
              ] else ...[
                Text(s.notClockedIn, style: Theme.of(context).textTheme.titleMedium),
                const SizedBox(height: 16),
                FilledButton.icon(
                  onPressed: () => _clockIn(context, ref),
                  icon: const Icon(Icons.login),
                  label: Text(s.clockIn),
                ),
              ],
            ],
          ),
        ),
        if (tc.recent.isNotEmpty) ...[
          const SizedBox(height: 16),
          Text(s.recentShifts, style: Theme.of(context).textTheme.titleSmall),
          const SizedBox(height: 8),
          GlassPanel(
            padding: const EdgeInsets.symmetric(vertical: 4),
            child: Material(
              type: MaterialType.transparency,
              child: Column(
                children: [
                  for (final shift in tc.recent)
                    ListTile(
                      title: Text(_fmt.format(shift.clockInAt)),
                      subtitle: Text(shift.clockOutAt == null
                          ? '—'
                          : _fmt.format(shift.clockOutAt!)),
                      trailing: shift.workedMinutes == null
                          ? null
                          : Text(s.durationLabel(shift.workedMinutes!)),
                    ),
                ],
              ),
            ),
          ),
        ],
      ],
    );
  }

  Future<void> _clockIn(BuildContext context, WidgetRef ref) async {
    try {
      await ref.read(timeclockRepositoryProvider).clockIn();
      ref.invalidate(myTimeclockProvider);
    } on ApiError catch (e) {
      if (context.mounted) _toast(context, e.message);
    }
  }

  Future<void> _clockOut(BuildContext context, WidgetRef ref) async {
    try {
      await ref.read(timeclockRepositoryProvider).clockOut();
      ref.invalidate(myTimeclockProvider);
    } on ApiError catch (e) {
      if (context.mounted) _toast(context, e.message);
    }
  }

  void _toast(BuildContext context, String message) {
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(message)));
  }
}
