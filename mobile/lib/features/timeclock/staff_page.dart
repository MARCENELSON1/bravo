import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import '../../api/api_error.dart';
import '../../l10n/strings.dart';
import '../../ui/app_background.dart';
import '../../ui/glass_panel.dart';
import '../../ui/state_views.dart';
import '../../util/money.dart';
import '../finance/finance_range.dart';
import 'staff_repository.dart';

/// Personal (paridad con `/app/staff` del web): reporte por empleado (horas,
/// extra, mesas, ventas, valor/hora editable) + turnos con ajuste. OWNER/MANAGER.
/// (La provisión de la pantalla de fichaje del web queda fuera por ahora.)
class StaffPage extends ConsumerStatefulWidget {
  const StaffPage({super.key});

  @override
  ConsumerState<StaffPage> createState() => _StaffPageState();
}

class _StaffPageState extends ConsumerState<StaffPage> {
  FinanceRange _range = FinanceRange.month;
  static final _dateFmt = DateFormat('dd/MM');
  static final _timeFmt = DateFormat('HH:mm');

  @override
  Widget build(BuildContext context) {
    final s = context.s;
    final report = ref.watch(staffReportProvider(_range));
    final shifts = ref.watch(shiftsProvider(_range));
    return Scaffold(
      backgroundColor: Colors.transparent,
      appBar: AppBar(
          title: Text(s.staffTitle), backgroundColor: Colors.transparent),
      body: Stack(
        children: [
          const AppBackground(),
          SafeArea(
            child: Column(
              children: [
                _rangeBar(s),
                Expanded(
                  child: RefreshIndicator(
                    onRefresh: () async {
                      ref.invalidate(staffReportProvider(_range));
                      ref.invalidate(shiftsProvider(_range));
                    },
                    child: ListView(
                      physics: const AlwaysScrollableScrollPhysics(),
                      padding: const EdgeInsets.all(16),
                      children: [
                        Text(s.staffReportTitle,
                            style: Theme.of(context).textTheme.titleSmall),
                        const SizedBox(height: 8),
                        _report(context, s, report),
                        const SizedBox(height: 20),
                        Text(s.staffShiftsTitle,
                            style: Theme.of(context).textTheme.titleSmall),
                        const SizedBox(height: 8),
                        _shifts(context, s, report, shifts),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _rangeBar(Strings s) => Padding(
        padding: const EdgeInsets.fromLTRB(12, 8, 12, 4),
        child: SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: Row(
            children: [
              for (final r in FinanceRange.values)
                Padding(
                  padding: const EdgeInsets.only(right: 8),
                  child: ChoiceChip(
                    label: Text(s.financeRange(r)),
                    selected: _range == r,
                    onSelected: (_) => setState(() => _range = r),
                  ),
                ),
            ],
          ),
        ),
      );

  Widget _report(
      BuildContext context, Strings s, AsyncValue<StaffReport> report) {
    return report.when(
      loading: () => const _Loading(),
      error: (e, _) => ErrorView(
          error: e, onRetry: () => ref.invalidate(staffReportProvider(_range))),
      data: (rep) {
        if (rep.rows.isEmpty) return GlassPanel(child: Text(s.staffNoReport));
        final scheme = Theme.of(context).colorScheme;
        return GlassPanel(
          padding: const EdgeInsets.symmetric(vertical: 4),
          child: Material(
            type: MaterialType.transparency,
            child: Column(
              children: [
                for (var i = 0; i < rep.rows.length; i++) ...[
                  if (i > 0) const Divider(height: 1),
                  ListTile(
                    title: Text(rep.rows[i].email,
                        maxLines: 1, overflow: TextOverflow.ellipsis),
                    subtitle: Text(
                      '${s.staffHours} ${s.formatMinutes(rep.rows[i].workedMinutes)}'
                      '${rep.rows[i].overtimeMinutes > 0 ? ' · ${s.staffOvertime} ${s.formatMinutes(rep.rows[i].overtimeMinutes)}' : ''}'
                      ' · ${s.staffTables} ${rep.rows[i].tablesServed}'
                      ' · ${formatMoney(rep.rows[i].salesAmount, rep.rows[i].currency)}',
                      style: TextStyle(
                          color: scheme.onSurfaceVariant, fontSize: 12),
                    ),
                    trailing: TextButton(
                      onPressed: () => _editRate(context, s, rep.rows[i]),
                      child: Text(
                        rep.rows[i].hourlyRateAmount != null
                            ? formatMoney(rep.rows[i].hourlyRateAmount!,
                                rep.rows[i].currency)
                            : s.staffRateNone,
                      ),
                    ),
                  ),
                ],
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _shifts(BuildContext context, Strings s,
      AsyncValue<StaffReport> report, AsyncValue<List<Shift>> shifts) {
    final emailByUser = <String, String>{
      for (final r in report.valueOrNull?.rows ?? const <StaffRow>[])
        r.userId: r.email,
    };
    String label(String userId) =>
        emailByUser[userId] ??
        (userId.length > 8 ? userId.substring(0, 8) : userId);

    return shifts.when(
      loading: () => const _Loading(),
      error: (e, _) => ErrorView(
          error: e, onRetry: () => ref.invalidate(shiftsProvider(_range))),
      data: (list) {
        if (list.isEmpty) return GlassPanel(child: Text(s.staffNoShifts));
        final scheme = Theme.of(context).colorScheme;
        return GlassPanel(
          padding: const EdgeInsets.symmetric(vertical: 4),
          child: Material(
            type: MaterialType.transparency,
            child: Column(
              children: [
                for (var i = 0; i < list.length; i++) ...[
                  if (i > 0) const Divider(height: 1),
                  _shiftTile(context, s, list[i], label(list[i].userId), scheme),
                ],
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _shiftTile(BuildContext context, Strings s, Shift sh, String who,
      ColorScheme scheme) {
    final inAt = DateTime.tryParse(sh.clockInAt)?.toLocal();
    final outAt = sh.clockOutAt == null
        ? null
        : DateTime.tryParse(sh.clockOutAt!)?.toLocal();
    final timeStr = inAt == null
        ? '—'
        : '${_dateFmt.format(inAt)} · ${_timeFmt.format(inAt)}'
            '→${outAt != null ? _timeFmt.format(outAt) : '—'}';
    return ListTile(
      title: Row(
        children: [
          Expanded(
              child: Text(who,
                  maxLines: 1, overflow: TextOverflow.ellipsis)),
          const SizedBox(width: 8),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
            decoration: BoxDecoration(
                color: scheme.surfaceContainerHighest,
                borderRadius: BorderRadius.circular(999)),
            child: Text(s.shiftSourceLabel(sh.source),
                style: const TextStyle(fontSize: 11)),
          ),
        ],
      ),
      subtitle: Text(timeStr,
          style: TextStyle(color: scheme.onSurfaceVariant, fontSize: 12)),
      trailing: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            sh.workedMinutes != null
                ? s.formatMinutes(sh.workedMinutes!)
                : s.staffInProgress,
            style: TextStyle(
                fontSize: 12,
                color: sh.workedMinutes != null
                    ? scheme.onSurface
                    : scheme.primary),
          ),
          IconButton(
            icon: const Icon(Icons.edit_calendar_outlined, size: 18),
            tooltip: s.staffAdjust,
            onPressed: () => _adjust(context, s, sh),
          ),
        ],
      ),
    );
  }

  Future<void> _editRate(BuildContext context, Strings s, StaffRow row) async {
    final controller = TextEditingController(
        text: row.hourlyRateAmount != null
            ? (row.hourlyRateAmount! / 100).toStringAsFixed(2)
            : '');
    final result = await showDialog<String>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(s.staffSetRate),
        content: TextField(
          controller: controller,
          autofocus: true,
          keyboardType: const TextInputType.numberWithOptions(decimal: true),
          decoration:
              InputDecoration(labelText: s.staffHourlyRate, prefixText: r'$ '),
        ),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(ctx), child: Text(s.cancel)),
          FilledButton(
              onPressed: () => Navigator.pop(ctx, controller.text.trim()),
              child: Text(s.setSave)),
        ],
      ),
    );
    if (result == null) return;
    final amount = result.isEmpty ? null : pesosToMinor(result);
    if (result.isNotEmpty && amount == null) {
      if (context.mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(s.staffInvalidRate)));
      }
      return;
    }
    try {
      await ref.read(staffRepositoryProvider).setHourlyRate(row.userId, amount);
      ref.invalidate(staffReportProvider(_range));
      if (context.mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(s.staffRateSaved)));
      }
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
            content: Text(e is ApiError ? e.message : s.staffRateError)));
      }
    }
  }

  Future<void> _adjust(BuildContext context, Strings s, Shift sh) async {
    var inAt = DateTime.tryParse(sh.clockInAt)?.toLocal() ?? DateTime.now();
    var outAt = sh.clockOutAt == null
        ? null
        : DateTime.tryParse(sh.clockOutAt!)?.toLocal();

    final saved = await showDialog<bool>(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setLocal) => AlertDialog(
          title: Text(s.staffAdjustTitle),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              ListTile(
                contentPadding: EdgeInsets.zero,
                title: Text(s.staffClockIn),
                subtitle: Text('${_dateFmt.format(inAt)} ${_timeFmt.format(inAt)}'),
                trailing: const Icon(Icons.edit),
                onTap: () async {
                  final picked = await _pickDateTime(ctx, inAt);
                  if (picked != null) setLocal(() => inAt = picked);
                },
              ),
              ListTile(
                contentPadding: EdgeInsets.zero,
                title: Text(s.staffClockOut),
                subtitle: Text(outAt != null
                    ? '${_dateFmt.format(outAt!)} ${_timeFmt.format(outAt!)}'
                    : '—'),
                trailing: const Icon(Icons.edit),
                onTap: () async {
                  final picked = await _pickDateTime(ctx, outAt ?? inAt);
                  if (picked != null) setLocal(() => outAt = picked);
                },
              ),
            ],
          ),
          actions: [
            TextButton(
                onPressed: () => Navigator.pop(ctx, false),
                child: Text(s.cancel)),
            FilledButton(
                onPressed: () => Navigator.pop(ctx, true),
                child: Text(s.setSave)),
          ],
        ),
      ),
    );
    if (saved != true) return;
    try {
      await ref.read(staffRepositoryProvider).adjustShift(
            sh.id,
            clockInAt: inAt.toUtc().toIso8601String(),
            clockOutAt: outAt?.toUtc().toIso8601String(),
          );
      ref.invalidate(shiftsProvider(_range));
      ref.invalidate(staffReportProvider(_range));
      if (context.mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(s.staffAdjusted)));
      }
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
            content: Text(e is ApiError ? e.message : s.staffAdjustError)));
      }
    }
  }

  Future<DateTime?> _pickDateTime(BuildContext context, DateTime initial) async {
    final date = await showDatePicker(
      context: context,
      initialDate: initial,
      firstDate: DateTime(2020),
      lastDate: DateTime.now().add(const Duration(days: 1)),
    );
    if (date == null || !context.mounted) return null;
    final time = await showTimePicker(
      context: context,
      initialTime: TimeOfDay.fromDateTime(initial),
    );
    if (time == null) return null;
    return DateTime(date.year, date.month, date.day, time.hour, time.minute);
  }
}

class _Loading extends StatelessWidget {
  const _Loading();
  @override
  Widget build(BuildContext context) => const Padding(
        padding: EdgeInsets.all(16),
        child: Center(child: CircularProgressIndicator()),
      );
}
