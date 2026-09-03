import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import '../../api/api_error.dart';
import '../../l10n/strings.dart';
import '../../ui/app_background.dart';
import '../../ui/glass_panel.dart';
import '../../ui/state_views.dart';
import '../floor/table_qr_repository.dart';
import 'reservations_repository.dart';

/// Reservas (paridad con `/app/reservations` del web): filtro por día/turno +
/// alta + acciones por estado (confirmar/sentar/completar/no-show/cancelar).
class ReservasPage extends ConsumerStatefulWidget {
  const ReservasPage({super.key});

  @override
  ConsumerState<ReservasPage> createState() => _ReservasPageState();
}

class _ReservasPageState extends ConsumerState<ReservasPage> {
  DateTime _day = DateTime.now();
  String? _turn; // null = todos
  static final _dayFmt = DateFormat('EEE dd/MM');
  static final _timeFmt = DateFormat('HH:mm');

  String get _dayStr => DateFormat('yyyy-MM-dd').format(_day);
  ReservationsQuery get _query => (day: _dayStr, turn: _turn);

  @override
  Widget build(BuildContext context) {
    final s = context.s;
    final async = ref.watch(reservationsProvider(_query));
    return Scaffold(
      backgroundColor: Colors.transparent,
      appBar: AppBar(
          title: Text(s.reservasTitle), backgroundColor: Colors.transparent),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _openForm(context),
        icon: const Icon(Icons.add),
        label: Text(s.reservaNew),
      ),
      body: Stack(
        children: [
          const AppBackground(),
          SafeArea(
            child: Column(
              children: [
                _filters(context, s),
                Expanded(
                  child: async.when(
                    loading: () =>
                        const Center(child: CircularProgressIndicator()),
                    error: (e, _) => ErrorView(
                        error: e,
                        onRetry: () =>
                            ref.invalidate(reservationsProvider(_query))),
                    data: (list) {
                      Future<void> refresh() async =>
                          ref.invalidate(reservationsProvider(_query));
                      if (list.isEmpty) {
                        return RefreshIndicator(
                          onRefresh: refresh,
                          child: ListView(
                            physics: const AlwaysScrollableScrollPhysics(),
                            children: [
                              SizedBox(
                                  height: 280,
                                  child: EmptyView(
                                      message: s.reservasEmpty,
                                      icon: Icons.event_available_outlined)),
                            ],
                          ),
                        );
                      }
                      return RefreshIndicator(
                        onRefresh: refresh,
                        child: ListView(
                          physics: const AlwaysScrollableScrollPhysics(),
                          padding: const EdgeInsets.fromLTRB(16, 8, 16, 96),
                          children: [
                            for (final r in list) _card(context, s, r),
                          ],
                        ),
                      );
                    },
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _filters(BuildContext context, Strings s) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(12, 8, 12, 4),
      child: Row(
        children: [
          OutlinedButton.icon(
            onPressed: () async {
              final picked = await showDatePicker(
                context: context,
                initialDate: _day,
                firstDate: DateTime(2020),
                lastDate: DateTime.now().add(const Duration(days: 365)),
              );
              if (picked != null) setState(() => _day = picked);
            },
            icon: const Icon(Icons.calendar_today, size: 16),
            label: Text(_dayFmt.format(_day)),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Row(
                children: [
                  for (final entry in [
                    (null, s.reservaAll),
                    ('LUNCH', s.turnLabel('LUNCH')),
                    ('DINNER', s.turnLabel('DINNER')),
                  ])
                    Padding(
                      padding: const EdgeInsets.only(right: 8),
                      child: ChoiceChip(
                        label: Text(entry.$2),
                        selected: _turn == entry.$1,
                        onSelected: (_) => setState(() => _turn = entry.$1),
                      ),
                    ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _card(BuildContext context, Strings s, Reservation r) {
    final scheme = Theme.of(context).colorScheme;
    final at = DateTime.tryParse(r.reservedAt)?.toLocal();
    final tables = ref.watch(tablesProvider).valueOrNull ?? const <TableItem>[];
    String tableLabel() {
      if (r.tableId == null) return '';
      for (final t in tables) {
        if (t.id == r.tableId) return ' · ${s.reservaTableOption(t.number)}';
      }
      return '';
    }

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
                Text(at != null ? _timeFmt.format(at) : '—',
                    style: const TextStyle(
                        fontWeight: FontWeight.w700, fontSize: 16)),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(r.customerName,
                      maxLines: 1, overflow: TextOverflow.ellipsis),
                ),
                _statusBadge(context, s, r.status),
              ],
            ),
            const SizedBox(height: 2),
            Text(
              '${r.partySize} ${s.reservaGuests.toLowerCase()} · ${s.turnLabel(r.turn)}${tableLabel()}'
              '${r.customerPhone != null ? ' · ${r.customerPhone}' : ''}',
              style: TextStyle(color: scheme.onSurfaceVariant, fontSize: 12),
            ),
            if (r.note != null && r.note!.isNotEmpty)
              Text(r.note!,
                  style:
                      TextStyle(color: scheme.onSurfaceVariant, fontSize: 12)),
            _actions(context, s, r),
          ],
        ),
      ),
    );
  }

  Widget _actions(BuildContext context, Strings s, Reservation r) {
    final buttons = <Widget>[];
    void add(String label, String action, {bool danger = false}) {
      buttons.add(TextButton(
        onPressed: () => _transition(context, s, r.id, action),
        style: danger
            ? TextButton.styleFrom(
                foregroundColor: Theme.of(context).colorScheme.error)
            : null,
        child: Text(label),
      ));
    }

    switch (r.status) {
      case 'PENDING':
        add(s.reservaConfirm, 'confirm');
        add(s.reservaSeat, 'seat');
        add(s.reservaNoShow, 'no-show', danger: true);
        add(s.cancel, 'cancel', danger: true);
      case 'CONFIRMED':
        add(s.reservaSeat, 'seat');
        add(s.reservaNoShow, 'no-show', danger: true);
        add(s.cancel, 'cancel', danger: true);
      case 'SEATED':
        add(s.reservaComplete, 'complete');
      default:
        return const SizedBox.shrink();
    }
    return Align(
      alignment: Alignment.centerLeft,
      child: Wrap(spacing: 4, children: buttons),
    );
  }

  Widget _statusBadge(BuildContext context, Strings s, String status) {
    final scheme = Theme.of(context).colorScheme;
    final color = switch (status) {
      'CONFIRMED' || 'SEATED' || 'COMPLETED' => scheme.primary,
      'CANCELLED' || 'NO_SHOW' => scheme.error,
      _ => scheme.onSurfaceVariant,
    };
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.15),
        borderRadius: BorderRadius.circular(999),
      ),
      child: Text(s.reservaStatusLabel(status),
          style: TextStyle(
              color: color, fontSize: 11, fontWeight: FontWeight.w600)),
    );
  }

  Future<void> _transition(
      BuildContext context, Strings s, String id, String action) async {
    try {
      await ref.read(reservationsRepositoryProvider).transition(id, action);
      ref.invalidate(reservationsProvider(_query));
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
            content:
                Text(e is ApiError ? e.message : s.reservaTransitionError)));
      }
    }
  }

  void _openForm(BuildContext context) {
    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (_) => _ReservationForm(day: _day, onCreated: () {
        ref.invalidate(reservationsProvider(_query));
      }),
    );
  }
}

class _ReservationForm extends ConsumerStatefulWidget {
  const _ReservationForm({required this.day, required this.onCreated});
  final DateTime day;
  final VoidCallback onCreated;
  @override
  ConsumerState<_ReservationForm> createState() => _ReservationFormState();
}

class _ReservationFormState extends ConsumerState<_ReservationForm> {
  final _name = TextEditingController();
  final _phone = TextEditingController();
  final _guests = TextEditingController(text: '2');
  final _note = TextEditingController();
  late DateTime _date = widget.day;
  TimeOfDay _time = const TimeOfDay(hour: 21, minute: 0);
  String _turn = 'DINNER';
  String? _tableId;
  bool _saving = false;

  @override
  void dispose() {
    _name.dispose();
    _phone.dispose();
    _guests.dispose();
    _note.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final s = context.s;
    final name = _name.text.trim();
    if (name.isEmpty) {
      _snack(s.reservaCustomerRequired);
      return;
    }
    final size = int.tryParse(_guests.text.trim());
    if (size == null || size < 1) {
      _snack(s.reservaGuestsInvalid);
      return;
    }
    final reservedAt = DateTime(_date.year, _date.month, _date.day, _time.hour,
            _time.minute)
        .toUtc()
        .toIso8601String();
    setState(() => _saving = true);
    try {
      await ref.read(reservationsRepositoryProvider).create(
            customerName: name,
            partySize: size,
            reservedAtIso: reservedAt,
            turn: _turn,
            customerPhone: _nn(_phone.text),
            tableId: _tableId,
            note: _nn(_note.text),
          );
      widget.onCreated();
      if (mounted) {
        Navigator.of(context).pop();
        _snack(s.reservaCreated);
      }
    } catch (e) {
      if (mounted) _snack(e is ApiError ? e.message : s.reservaError);
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  void _snack(String m) => ScaffoldMessenger.of(context)
      .showSnackBar(SnackBar(content: Text(m)));
  String? _nn(String v) => v.trim().isEmpty ? null : v.trim();

  @override
  Widget build(BuildContext context) {
    final s = context.s;
    final tables = ref.watch(tablesProvider).valueOrNull ?? const <TableItem>[];
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
              Text(s.reservaNew, style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: 12),
              TextField(
                  controller: _name,
                  decoration: InputDecoration(labelText: s.reservaCustomer)),
              const SizedBox(height: 12),
              TextField(
                  controller: _phone,
                  keyboardType: TextInputType.phone,
                  decoration: InputDecoration(labelText: s.reservaPhone)),
              const SizedBox(height: 12),
              Row(
                children: [
                  SizedBox(
                    width: 110,
                    child: TextField(
                        controller: _guests,
                        keyboardType: TextInputType.number,
                        decoration: InputDecoration(labelText: s.reservaGuests)),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: DropdownButtonFormField<String>(
                      initialValue: _turn,
                      decoration: InputDecoration(labelText: s.reservaShift),
                      items: [
                        for (final tv in ['LUNCH', 'DINNER'])
                          DropdownMenuItem(
                              value: tv, child: Text(s.turnLabel(tv))),
                      ],
                      onChanged: (v) => setState(() => _turn = v ?? _turn),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: () async {
                        final picked = await showDatePicker(
                          context: context,
                          initialDate: _date,
                          firstDate: DateTime.now()
                              .subtract(const Duration(days: 1)),
                          lastDate:
                              DateTime.now().add(const Duration(days: 365)),
                        );
                        if (picked != null) setState(() => _date = picked);
                      },
                      icon: const Icon(Icons.calendar_today, size: 16),
                      label: Text(DateFormat('dd/MM').format(_date)),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: () async {
                        final picked = await showTimePicker(
                            context: context, initialTime: _time);
                        if (picked != null) setState(() => _time = picked);
                      },
                      icon: const Icon(Icons.schedule, size: 16),
                      label: Text(_time.format(context)),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              DropdownButtonFormField<String?>(
                initialValue: _tableId,
                decoration: InputDecoration(labelText: s.reservaTable),
                items: [
                  DropdownMenuItem(value: null, child: Text(s.reservaNoTable)),
                  for (final t in tables)
                    DropdownMenuItem(
                        value: t.id,
                        child: Text(s.reservaTableOption(t.number))),
                ],
                onChanged: (v) => setState(() => _tableId = v),
              ),
              const SizedBox(height: 12),
              TextField(
                  controller: _note,
                  decoration: InputDecoration(labelText: s.reservaNote)),
              const SizedBox(height: 16),
              FilledButton.icon(
                onPressed: _saving ? null : _submit,
                icon: const Icon(Icons.check),
                label: Text(s.reservaNew),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
