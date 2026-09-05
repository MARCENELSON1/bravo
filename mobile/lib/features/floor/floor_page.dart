import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:uuid/uuid.dart';

import '../../api/api_error.dart';
import '../../auth/session_notifier.dart';
import '../../l10n/strings.dart';
import '../../theme/colors.dart';
import '../../ui/state_views.dart';
import '../../util/money.dart';
import '../cashier/cobro_sheet.dart';
import '../order/order_page.dart';
import 'floor_dtos.dart';
import 'floor_filter.dart';
import 'floor_ops.dart';
import 'floor_providers.dart';
import 'floor_quick_actions.dart';
import 'floor_view.dart';
import 'pending_qr_tray.dart';
import 'table_card.dart';

/// Plano de salón en vivo. Espeja `frontend/src/features/floor/floor-page.tsx`
/// (grilla por sector, chips de filtro, tira de "requieren atención") y suma
/// lo que hace al mozo rápido: resumen operativo arriba, orden por urgencia,
/// acciones desde el plano (long-press y chips que resuelven), pulso cuando
/// una mesa pasa a pedir atención, grilla adaptativa.
class FloorPage extends ConsumerStatefulWidget {
  const FloorPage({super.key});

  @override
  ConsumerState<FloorPage> createState() => _FloorPageState();
}

class _FloorPageState extends ConsumerState<FloorPage> {
  final _search = TextEditingController();
  FloorFilter _filter = FloorFilter.all;
  Timer? _tick;

  // Pulso: qué mesas acaban de pasar a pedir atención (se limpia solo).
  Map<String, bool> _attention = const {};
  Set<String> _flash = const {};
  Timer? _flashClear;

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
    _flashClear?.cancel();
    _search.dispose();
    super.dispose();
  }

  /// Detecta las mesas que PASARON a atención con este refresco y las hace
  /// pulsar ~1.5 s. Se compara contra el snapshot anterior, así lo viejo no
  /// molesta y lo nuevo se nota aunque nadie esté mirando el plano.
  void _trackAttention(List<FloorTable> tables) {
    if (_attention.isEmpty) {
      _attention = attentionSnapshot(tables);
      return;
    }
    final fresh = newlyAttention(_attention, tables);
    _attention = attentionSnapshot(tables);
    if (fresh.isEmpty) return;
    HapticFeedback.lightImpact();
    _flash = {..._flash, ...fresh};
    _flashClear?.cancel();
    _flashClear = Timer(const Duration(milliseconds: 1500), () {
      if (mounted) setState(() => _flash = const {});
    });
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
      data: (tables) {
        _trackAttention(tables);
        return _content(context, s, tables, sectors, userId);
      },
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
              .where(
                (t) =>
                    t.number.toString().contains(q) ||
                    (t.name?.toLowerCase().contains(q) ?? false),
              )
              .toList();
    final visible = filterFloor(searched, _filter, userId);
    final attention = sortByUrgency(
      searched.where((t) => floorView(t).attention).toList(),
    );

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
          const SizedBox(height: 12),
          _summary(context, s, summarizeFloor(tables, userId)),
          const SizedBox(height: 12),
          const PendingQrTray(),
          if (attention.isNotEmpty) ...[
            const SizedBox(height: 14),
            Text(
              s.floorAttention(attention.length),
              style: Theme.of(context).textTheme.titleSmall,
            ),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                for (final t in attention) _attentionChip(context, s, t),
              ],
            ),
          ],
          const SizedBox(height: 16),
          ..._sectorSections(s, visible, sectors),
        ],
      ),
    );
  }

  /// Foco del mozo de un vistazo: mías · para servir · $ de mis mesas.
  Widget _summary(BuildContext context, Strings s, FloorSummary sum) {
    Widget stat(String n, String label, {bool hot = false}) {
      final theme = Theme.of(context);
      return Expanded(
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 9),
          decoration: BoxDecoration(
            color: hot
                ? WellnodPalette.warn.withValues(alpha: 0.12)
                : theme.colorScheme.surface.withValues(alpha: 0.5),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(
              color: hot
                  ? WellnodPalette.warn.withValues(alpha: 0.45)
                  : theme.colorScheme.outlineVariant.withValues(alpha: 0.5),
            ),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                n,
                style: theme.textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.w800,
                  color: hot ? WellnodPalette.warn : null,
                  fontFeatures: const [FontFeature.tabularFigures()],
                ),
              ),
              Text(
                label,
                style: theme.textTheme.labelSmall?.copyWith(
                  color: theme.colorScheme.onSurfaceVariant,
                ),
              ),
            ],
          ),
        ),
      );
    }

    return Row(
      children: [
        stat('${sum.mine}', s.floorSummaryMine),
        const SizedBox(width: 8),
        stat('${sum.toServe}', s.floorSummaryToServe, hot: sum.toServe > 0),
        const SizedBox(width: 8),
        stat(formatMoney(sum.mineTotal, 'ARS'), s.floorSummaryMyTables),
      ],
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

  /// Chip que RESUELVE: "Salón 3 · Servir" sirve; "· Cobrar" abre el cobro.
  /// Si la acción no aplica, abre la mesa (comportamiento anterior).
  Widget _attentionChip(BuildContext context, Strings s, FloorTable t) {
    final v = floorView(t);
    final name = t.name ?? t.number.toString();
    final canServe =
        v.status == FloorStatus.toServe && (t.activeOrder?.readyCount ?? 0) > 0;
    final label = canServe
        ? '$name · ${s.quickServeShort}'
        : v.status == FloorStatus.toCharge && t.activeOrder != null
        ? '$name · ${s.cobro}'
        : '$name · ${s.floorState(v.status)}';
    return ActionChip(
      avatar: Icon(
        canServe ? Icons.room_service_outlined : Icons.payments_outlined,
        size: 16,
        color: WellnodPalette.warn,
      ),
      label: Text(label),
      onPressed: () {
        HapticFeedback.selectionClick();
        if (canServe) {
          _serve(t);
        } else if (v.status == FloorStatus.toCharge && t.activeOrder != null) {
          _charge(t);
        } else {
          _open(t);
        }
      },
    );
  }

  List<Widget> _sectorSections(
    Strings s,
    List<FloorTable> visible,
    List<Sector> sectors,
  ) {
    if (visible.isEmpty) {
      return [
        Padding(
          padding: const EdgeInsets.all(24),
          child: Center(child: Text(s.floorEmpty)),
        ),
      ];
    }
    if (sectors.isEmpty) return [_grid(sortByUrgency(visible))];

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
      widgets.add(_grid(sortByUrgency(inSec)));
    }
    final orphans = visible.where((t) => !used.contains(t.id)).toList();
    if (orphans.isNotEmpty) {
      widgets.add(_sectionHeader('—', orphans.length, null));
      widgets.add(_grid(sortByUrgency(orphans)));
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
          Text(
            '· $count',
            style: TextStyle(
              color: Theme.of(context).colorScheme.onSurfaceVariant,
            ),
          ),
        ],
      ),
    );
  }

  /// Grilla adaptativa: 2 columnas en teléfono vertical, más en horizontal /
  /// tablet (una card cada ~180 px).
  Widget _grid(List<FloorTable> tables) {
    return LayoutBuilder(
      builder: (ctx, c) {
        const gap = 12.0;
        final cols = (c.maxWidth / 180).floor().clamp(2, 6);
        final w = (c.maxWidth - gap * (cols - 1)) / cols;
        return Padding(
          padding: const EdgeInsets.only(bottom: 8),
          child: Wrap(
            spacing: gap,
            runSpacing: gap,
            children: [
              for (final t in tables)
                SizedBox(
                  width: w,
                  child: TableCard(
                    table: t,
                    flash: _flash.contains(t.id),
                    onOpen: () => _open(t),
                    onLongPress: () => _quickActions(t),
                    onBill:
                        (!(t.activeOrder?.isPrepaidServed ?? false) &&
                            _canBill(t))
                        ? () => _bill(t)
                        : null,
                    // Autoservicio ya pago y servido: "Liberar" en vez de "Cobrar".
                    onFree: (t.activeOrder?.isPrepaidServed ?? false)
                        ? () => _free(t)
                        : null,
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

  // --- Acciones desde el plano ---

  /// Long-press: menú rápido con lo que la mesa pide arriba y en ámbar.
  Future<void> _quickActions(FloorTable t) async {
    HapticFeedback.mediumImpact();
    final order = t.activeOrder;
    final v = floorView(t);
    final actions = <QuickAction>[];
    QuickAction? primary;
    if (order != null && order.readyCount > 0) {
      actions.add(QuickAction.serve);
      primary = QuickAction.serve;
    }
    if (order != null && order.pendingCount > 0) actions.add(QuickAction.march);
    if (order != null && !order.isPrepaidServed) {
      actions.add(QuickAction.charge);
      if (v.status == FloorStatus.toCharge) primary ??= QuickAction.charge;
    }
    if (order?.isPrepaidServed ?? false) {
      actions.add(QuickAction.free);
      primary ??= QuickAction.free;
    }
    if (!(order?.isPrepaidServed ?? false) && _canBill(t)) {
      actions.add(QuickAction.bill);
    }
    if (order != null && t.session?.waiterId == null) {
      actions.add(QuickAction.claim);
    }
    actions.add(QuickAction.open);

    final chosen = await showFloorQuickActions(
      context,
      table: t,
      actions: actions,
      primary: primary,
    );
    if (chosen == null || !mounted) return;
    switch (chosen) {
      case QuickAction.serve:
        return _serve(t);
      case QuickAction.march:
        return _march(t);
      case QuickAction.charge:
        return _charge(t);
      case QuickAction.bill:
        return _bill(t);
      case QuickAction.free:
        return _free(t);
      case QuickAction.claim:
        return _claim(t);
      case QuickAction.open:
        return _open(t);
    }
  }

  Future<void> _open(FloorTable t) async {
    try {
      final orderId =
          t.activeOrder?.id ??
          await ref
              .read(orderRepositoryProvider)
              .create(tableId: t.id, id: const Uuid().v4());
      if (!mounted) return;
      await Navigator.of(context)
          .push(MaterialPageRoute(builder: (_) => OrderPage(orderId: orderId)));
      if (mounted) ref.read(floorProvider.notifier).refresh();
    } on ApiError catch (e) {
      _toast(e.message);
    }
  }

  Future<void> _serve(FloorTable t) async {
    final orderId = t.activeOrder?.id;
    if (orderId == null) return;
    final done = context.s.readyServedDone;
    try {
      HapticFeedback.mediumImpact();
      await ref.read(orderRepositoryProvider).markServed(orderId);
      ref.read(floorProvider.notifier).refresh();
      _toast(done);
    } on ApiError catch (e) {
      _toast(e.message);
    }
  }

  Future<void> _march(FloorTable t) async {
    final orderId = t.activeOrder?.id;
    if (orderId == null) return;
    try {
      HapticFeedback.mediumImpact();
      await ref.read(orderRepositoryProvider).send(orderId);
      ref.read(floorProvider.notifier).refresh();
    } on ApiError catch (e) {
      _toast(e.message);
    }
  }

  void _charge(FloorTable t) {
    final orderId = t.activeOrder?.id;
    if (orderId == null) return;
    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (_) => SizedBox(
        height: MediaQuery.of(context).size.height * 0.85,
        child: CobroSheet(orderId: orderId),
      ),
    ).then((_) {
      if (mounted) ref.read(floorProvider.notifier).refresh();
    });
  }

  Future<void> _claim(FloorTable t) async {
    final orderId = t.activeOrder?.id;
    if (orderId == null) return;
    final done = context.s.claimDone;
    try {
      await ref.read(orderRepositoryProvider).claim(orderId);
      ref.read(floorProvider.notifier).refresh();
      _toast(done);
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

  Future<void> _free(FloorTable t) async {
    final orderId = t.activeOrder?.id;
    if (orderId == null) return;
    try {
      await ref.read(orderRepositoryProvider).free(orderId);
      ref.read(floorProvider.notifier).refresh();
    } on ApiError catch (e) {
      _toast(e.message);
    }
  }

  void _toast(String message) {
    if (!mounted) return;
    ScaffoldMessenger.of(context)
        .showSnackBar(SnackBar(content: Text(message)));
  }
}
