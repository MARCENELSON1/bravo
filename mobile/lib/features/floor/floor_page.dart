import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:uuid/uuid.dart';

import '../../api/api_error.dart';
import '../../auth/session_notifier.dart';
import '../../l10n/strings.dart';
import '../../ui/state_views.dart';
import '../order/order_page.dart';
import 'floor_dtos.dart';
import 'floor_filter.dart';
import 'floor_providers.dart';
import 'floor_view.dart';
import 'pending_qr_tray.dart';
import 'table_card.dart';

/// Plano de salón en vivo (Tanda 1). Espeja `frontend/src/features/floor/floor-page.tsx`:
/// grilla de cards por sector, chips de filtro y tira de "requieren atención".
class FloorPage extends ConsumerStatefulWidget {
  const FloorPage({super.key});

  @override
  ConsumerState<FloorPage> createState() => _FloorPageState();
}

class _FloorPageState extends ConsumerState<FloorPage> {
  final _search = TextEditingController();
  FloorFilter _filter = FloorFilter.all;
  Timer? _tick;

  @override
  void initState() {
    super.initState();
    // Re-render cada 30s para actualizar los timers entre refetches.
    _tick = Timer.periodic(const Duration(seconds: 30), (_) {
      if (mounted) setState(() {});
    });
    _search.addListener(() {
      if (mounted) setState(() {});
    });
  }

  @override
  void dispose() {
    _tick?.cancel();
    _search.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final s = context.s;
    final async = ref.watch(floorProvider);
    final sectors = ref.watch(sectorsProvider).valueOrNull ?? const <Sector>[];
    final sessionState = ref.watch(sessionProvider);
    final userId = sessionState is SessionAuthenticated
        ? sessionState.session.userId
        : null;

    return async.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (e, _) => ErrorView(
        error: e,
        onRetry: () => ref.read(floorProvider.notifier).refresh(),
      ),
      data: (tables) => _content(context, s, tables, sectors, userId),
    );
  }

  Widget _content(
    BuildContext context,
    Strings s,
    List<FloorTable> tables,
    List<Sector> sectors,
    String? userId,
  ) {
    final q = _search.text.trim().toLowerCase();
    final searched = q.isEmpty
        ? tables
        : tables
            .where((t) =>
                t.number.toString().contains(q) ||
                (t.name?.toLowerCase().contains(q) ?? false))
            .toList();
    final visible = filterFloor(searched, _filter, userId);
    final attention = searched.where((t) => floorView(t).attention).toList();

    return RefreshIndicator(
      onRefresh: () => ref.read(floorProvider.notifier).refresh(),
      child: ListView(
        padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
        children: [
          TextField(
            controller: _search,
            decoration: InputDecoration(
              hintText: s.floorSearch,
              prefixIcon: const Icon(Icons.search),
            ),
          ),
          const SizedBox(height: 12),
          _chips(s),
          const SizedBox(height: 14),
          const PendingQrTray(),
          if (attention.isNotEmpty) ...[
            const SizedBox(height: 14),
            Text(s.floorAttention(attention.length),
                style: Theme.of(context).textTheme.titleSmall),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [for (final t in attention) _attentionChip(context, t)],
            ),
          ],
          const SizedBox(height: 16),
          ..._sectorSections(s, visible, sectors),
        ],
      ),
    );
  }

  Widget _chips(Strings s) {
    final items = <FloorFilter, String>{
      FloorFilter.all: s.chipAll,
      FloorFilter.toServe: s.chipToServe,
      FloorFilter.toCharge: s.chipToCharge,
      FloorFilter.mine: s.chipMine,
      FloorFilter.free: s.chipFree,
    };
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: Row(
        children: [
          for (final e in items.entries)
            Padding(
              padding: const EdgeInsets.only(right: 8),
              child: ChoiceChip(
                label: Text(e.value),
                selected: _filter == e.key,
                onSelected: (_) => setState(() => _filter = e.key),
              ),
            ),
        ],
      ),
    );
  }

  Widget _attentionChip(BuildContext context, FloorTable t) {
    final v = floorView(t);
    return ActionChip(
      label: Text('${t.name ?? t.number} · ${context.s.floorState(v.status)}'),
      onPressed: () => _open(t),
    );
  }

  List<Widget> _sectorSections(
      Strings s, List<FloorTable> visible, List<Sector> sectors) {
    if (visible.isEmpty) {
      return [
        Padding(
          padding: const EdgeInsets.all(24),
          child: Center(child: Text(s.floorEmpty)),
        ),
      ];
    }
    if (sectors.isEmpty) return [_grid(visible)];

    final widgets = <Widget>[];
    final used = <String>{};
    final ordered = [...sectors]
      ..sort((a, b) => a.sortOrder.compareTo(b.sortOrder));
    for (final sec in ordered) {
      final inSec = visible.where((t) => t.sectorId == sec.id).toList();
      if (inSec.isEmpty) continue;
      for (final t in inSec) {
        used.add(t.id);
      }
      widgets.add(_sectionHeader(sec.name, inSec.length, sec.color));
      widgets.add(_grid(inSec));
    }
    final orphans = visible.where((t) => !used.contains(t.id)).toList();
    if (orphans.isNotEmpty) {
      widgets.add(_sectionHeader('—', orphans.length, null));
      widgets.add(_grid(orphans));
    }
    return widgets;
  }

  Widget _sectionHeader(String name, int count, String? color) {
    Color? dot;
    if (color != null) {
      final hex = color.replaceFirst('#', '');
      final v = int.tryParse(hex.length == 6 ? 'FF$hex' : hex, radix: 16);
      if (v != null) dot = Color(v);
    }
    return Padding(
      padding: const EdgeInsets.only(top: 8, bottom: 8),
      child: Row(
        children: [
          if (dot != null) ...[
            Container(
              width: 10,
              height: 10,
              decoration: BoxDecoration(color: dot, shape: BoxShape.circle),
            ),
            const SizedBox(width: 8),
          ],
          Text(name, style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(width: 6),
          Text('· $count',
              style: TextStyle(
                  color: Theme.of(context).colorScheme.onSurfaceVariant)),
        ],
      ),
    );
  }

  Widget _grid(List<FloorTable> tables) {
    return LayoutBuilder(
      builder: (ctx, c) {
        final w = (c.maxWidth - 12) / 2;
        return Padding(
          padding: const EdgeInsets.only(bottom: 8),
          child: Wrap(
            spacing: 12,
            runSpacing: 12,
            children: [
              for (final t in tables)
                SizedBox(
                  width: w,
                  child: TableCard(
                    table: t,
                    onOpen: () => _open(t),
                    onBill: _canBill(t) ? () => _bill(t) : null,
                  ),
                ),
            ],
          ),
        );
      },
    );
  }

  bool _canBill(FloorTable t) {
    if (t.isFree || t.session == null) return false;
    final st = floorView(t).status;
    return st != FloorStatus.toCharge &&
        st != FloorStatus.closed &&
        st != FloorStatus.free;
  }

  Future<void> _open(FloorTable t) async {
    try {
      final orderId = t.activeOrder?.id ??
          await ref
              .read(orderRepositoryProvider)
              .create(tableId: t.id, id: const Uuid().v4());
      if (!mounted) return;
      await Navigator.of(context).push(
        MaterialPageRoute(builder: (_) => OrderPage(orderId: orderId)),
      );
      if (mounted) ref.read(floorProvider.notifier).refresh();
    } on ApiError catch (e) {
      _toast(e.message);
    }
  }

  Future<void> _bill(FloorTable t) async {
    final sessionId = t.session?.id;
    if (sessionId == null) return;
    try {
      await ref.read(floorRepositoryProvider).requestBill(sessionId);
      ref.read(floorProvider.notifier).refresh();
    } on ApiError catch (e) {
      _toast(e.message);
    }
  }

  void _toast(String message) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(message)));
  }
}
