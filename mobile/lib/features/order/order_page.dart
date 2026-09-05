import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/api_error.dart';
import '../../data/offline/sync_indicator.dart';
import '../../data/printing/escpos_ticket.dart';
import '../../data/printing/printer_providers.dart';
import '../../l10n/strings.dart';
import '../../theme/colors.dart';
import '../../ui/app_background.dart';
import '../../ui/glass_panel.dart';
import '../../util/money.dart';
import '../cashier/cobro_sheet.dart';
import '../floor/floor_dtos.dart';
import '../floor/floor_providers.dart';
import '../settings/printer_page.dart';
import 'capture_grid.dart';
import 'order_dtos.dart';
import 'order_providers.dart';
import 'product_dtos.dart';
import 'item_options_sheet.dart';

/// Comanda del mozo como pantalla de captura tipo POS (una sola pantalla):
/// ticket colapsable arriba (por estación) → grilla de productos con badges
/// (abre en "★ Frecuentes") → barra de acción fija abajo (Marchar / Servir
/// según el estado + Cobrar). Nunca se sale de acá para cargar. Captura
/// optimista con cola offline; mover/unir/tomar mesa quedan en el menú.
class OrderPage extends ConsumerStatefulWidget {
  const OrderPage({super.key, required this.orderId});

  final String orderId;

  @override
  ConsumerState<OrderPage> createState() => _OrderPageState();
}

class _OrderPageState extends ConsumerState<OrderPage> {
  String get orderId => widget.orderId;
  bool _ticketOpen = true;

  @override
  Widget build(BuildContext context) {
    final s = context.s;
    final async = ref.watch(orderControllerProvider(orderId));
    final tables = ref.watch(floorProvider).valueOrNull ?? const <FloorTable>[];

    return Scaffold(
      backgroundColor: Colors.transparent,
      appBar: AppBar(
        title: Text(_title(s, async.valueOrNull, tables)),
        backgroundColor: Colors.transparent,
        actions: [
          const SyncIndicator(),
          IconButton(
            icon: const Icon(Icons.print_outlined),
            onPressed: () => Navigator.of(context)
                .push(MaterialPageRoute(builder: (_) => const PrinterPage())),
          ),
          PopupMenuButton<String>(
            onSelected: (v) {
              switch (v) {
                case 'fire_all':
                  _fireAll();
                case 'claim':
                  _claim(s);
                case 'move':
                  _moveToFree();
                case 'merge':
                  _mergeHere();
              }
            },
            itemBuilder: (_) => [
              // "Traé todo junto": solo cuando hay cursos en espera.
              if ((async.valueOrNull?.heldCount ?? 0) > 0)
                PopupMenuItem(value: 'fire_all', child: Text(s.fireAll)),
              PopupMenuItem(value: 'claim', child: Text(s.claimTable)),
              PopupMenuItem(value: 'move', child: Text(s.moveTable)),
              PopupMenuItem(value: 'merge', child: Text(s.mergeTable)),
            ],
          ),
        ],
      ),
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
              data: (order) => _content(context, s, order),
            ),
          ),
        ],
      ),
    );
  }

  /// "Mesa 4" (o el nombre de la mesa) en vez de un genérico "Comanda".
  String _title(Strings s, Order? order, List<FloorTable> tables) {
    if (order == null) return s.orderTitle;
    for (final t in tables) {
      if (t.id == order.tableId) return t.name ?? s.tableLabel(t.number);
    }
    return s.orderTitle;
  }

  Widget _content(BuildContext context, Strings s, Order order) {
    return Column(
      children: [
        _ticket(context, s, order),
        Expanded(
          child: CaptureGrid(
            order: order,
            onAdd: _add,
            onAddWithOptions: _addWithOptions,
          ),
        ),
        _actionBar(context, s, order),
      ],
    );
  }

  // --- Ticket (la comanda que se está armando), agrupado por curso ---

  Widget _ticket(BuildContext context, Strings s, Order order) {
    final theme = Theme.of(context);
    final items = order.liveItems;
    // Cursos presentes, en orden de servicio (bebidas → entrada → principal → postre).
    final courses = Course.values
        .where((c) => items.any((i) => i.course == c))
        .toList();

    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 0),
      child: GlassPanel(
        blur: false,
        padding: EdgeInsets.zero,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            InkWell(
              onTap: () => setState(() => _ticketOpen = !_ticketOpen),
              borderRadius: BorderRadius.circular(16),
              child: Padding(
                padding: const EdgeInsets.fromLTRB(14, 10, 8, 10),
                child: Row(
                  children: [
                    Icon(
                      Icons.receipt_long_outlined,
                      size: 18,
                      color: theme.colorScheme.onSurfaceVariant,
                    ),
                    const SizedBox(width: 8),
                    Text(
                      items.isEmpty
                          ? s.orderEmpty
                          : s.ticketItems(items.length),
                      style: theme.textTheme.bodyMedium,
                    ),
                    const Spacer(),
                    Text(
                      formatMoney(order.totalAmount, order.currency),
                      style: theme.textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    Icon(
                      _ticketOpen ? Icons.expand_less : Icons.expand_more,
                      color: theme.colorScheme.onSurfaceVariant,
                    ),
                  ],
                ),
              ),
            ),
            if (items.isEmpty)
              Padding(
                padding: const EdgeInsets.fromLTRB(14, 0, 14, 10),
                child: Text(
                  s.captureHint,
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: theme.colorScheme.onSurfaceVariant,
                  ),
                ),
              ),
            if (_ticketOpen && items.isNotEmpty)
              ConstrainedBox(
                constraints: BoxConstraints(
                  maxHeight: MediaQuery.of(context).size.height * 0.38,
                ),
                child: ListView(
                  shrinkWrap: true,
                  padding: const EdgeInsets.only(bottom: 6),
                  children: [
                    const Divider(height: 1),
                    for (final c in courses) ...[
                      _courseHeader(context, s, order, c),
                      for (final it in items.where((i) => i.course == c))
                        _ticketRow(context, s, order, it),
                    ],
                    if (order.heldCount > 0)
                      Padding(
                        padding: const EdgeInsets.fromLTRB(14, 6, 14, 4),
                        child: Text(
                          s.courseHint,
                          style: theme.textTheme.bodySmall?.copyWith(
                            color: theme.colorScheme.onSurfaceVariant,
                          ),
                        ),
                      ),
                  ],
                ),
              ),
          ],
        ),
      ),
    );
  }

  /// Cabecera de un curso: nombre + estado, y la acción que le toca
  /// ("Marchar principales" si es el próximo en espera; "Servir" si está listo).
  Widget _courseHeader(BuildContext context, Strings s, Order order, Course c) {
    final theme = Theme.of(context);
    final st = order.courseState(c);
    final isNext = order.nextCourse == c;
    final ready = st == CourseState.ready;
    final Color accent = switch (st) {
      CourseState.ready => WellnodPalette.warn,
      CourseState.inKitchen => theme.colorScheme.primary,
      CourseState.served => const Color(0xFF10B981),
      _ => theme.colorScheme.onSurfaceVariant,
    };
    return Padding(
      padding: const EdgeInsets.fromLTRB(14, 10, 10, 2),
      child: Row(
        children: [
          Text(
            s.courseLabel(c).toUpperCase(),
            style: theme.textTheme.labelSmall?.copyWith(
              color: theme.colorScheme.onSurfaceVariant,
              letterSpacing: 0.8,
              fontWeight: FontWeight.w700,
            ),
          ),
          if (st != null) ...[
            const SizedBox(width: 8),
            Text(
              s.courseStateLabel(st),
              style: theme.textTheme.labelSmall?.copyWith(
                color: accent,
                fontWeight: FontWeight.w600,
              ),
            ),
          ],
          const Spacer(),
          if (ready)
            _courseAction(
              context,
              s.serveCourse(c),
              Icons.room_service_outlined,
              WellnodPalette.warn,
              () => _serveCourse(c),
            )
          else if (isNext)
            _courseAction(
              context,
              s.fireCourse(c),
              Icons.send,
              theme.colorScheme.primary,
              _fireNext,
            ),
        ],
      ),
    );
  }

  Widget _courseAction(
    BuildContext context,
    String label,
    IconData icon,
    Color color,
    VoidCallback onTap,
  ) {
    return ActionChip(
      visualDensity: VisualDensity.compact,
      avatar: Icon(icon, size: 15, color: color),
      label: Text(
        label,
        style: TextStyle(
          color: color,
          fontWeight: FontWeight.w700,
          fontSize: 12,
        ),
      ),
      side: BorderSide(color: color.withValues(alpha: 0.5)),
      onPressed: () {
        HapticFeedback.mediumImpact();
        onTap();
      },
    );
  }

  Widget _ticketRow(
    BuildContext context,
    Strings s,
    Order order,
    OrderItem it,
  ) {
    final theme = Theme.of(context);
    final muted = theme.colorScheme.onSurfaceVariant;
    final pending = it.status.isPending;
    final detail = _detail(it);
    return InkWell(
      onTap: pending ? () => _editLine(it) : null,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 7),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    '${it.quantity}× ${it.name}',
                    style: theme.textTheme.bodyMedium?.copyWith(
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                  if (detail != null)
                    Text(
                      detail,
                      style: theme.textTheme.bodySmall?.copyWith(color: muted),
                    ),
                  if (!pending)
                    Padding(
                      padding: const EdgeInsets.only(top: 2),
                      child: Text(
                        s.itemStatusLabel(it.status),
                        style: theme.textTheme.labelSmall?.copyWith(
                          color: theme.colorScheme.primary,
                        ),
                      ),
                    ),
                ],
              ),
            ),
            const SizedBox(width: 8),
            Text(
              formatMoney(it.lineTotal, order.currency),
              style: theme.textTheme.bodyMedium,
            ),
            if (pending) Icon(Icons.chevron_right, size: 18, color: muted),
          ],
        ),
      ),
    );
  }

  String? _detail(OrderItem it) {
    if (it.selectedOptions.isNotEmpty) {
      return it.selectedOptions.map((o) => o.name).join(', ');
    }
    if (it.note != null && it.note!.isNotEmpty) return it.note;
    return null;
  }

  /// Tap en una línea pendiente: cantidad + nota ("cómo se quiere el plato")
  /// + quitar. Solo antes de marchar: después la cocina ya la leyó.
  Future<void> _editLine(OrderItem it) async {
    final s = context.s;
    var qty = it.quantity;
    var course = it.course;
    final noteCtrl = TextEditingController(text: it.note ?? '');
    final result = await showModalBottomSheet<String>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setSheet) {
          final theme = Theme.of(ctx);
          return Padding(
            padding: EdgeInsets.fromLTRB(
              20,
              0,
              20,
              MediaQuery.of(ctx).viewInsets.bottom + 20,
            ),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Text(
                  it.name,
                  style: theme.textTheme.titleLarge?.copyWith(
                    fontWeight: FontWeight.w700,
                  ),
                ),
                const SizedBox(height: 12),
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    IconButton.outlined(
                      iconSize: 28,
                      icon: const Icon(Icons.remove),
                      onPressed: qty > 1 ? () => setSheet(() => qty--) : null,
                    ),
                    SizedBox(
                      width: 80,
                      child: Text(
                        '$qty',
                        textAlign: TextAlign.center,
                        style: theme.textTheme.displaySmall?.copyWith(
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ),
                    IconButton.filled(
                      iconSize: 28,
                      icon: const Icon(Icons.add),
                      onPressed: () => setSheet(() => qty++),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                // Override del curso ("la provoleta como principal").
                Wrap(
                  spacing: 8,
                  children: [
                    for (final c in Course.values)
                      ChoiceChip(
                        label: Text(s.courseLabel(c)),
                        selected: course == c,
                        onSelected: (_) => setSheet(() => course = c),
                      ),
                  ],
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: noteCtrl,
                  textCapitalization: TextCapitalization.sentences,
                  decoration: InputDecoration(
                    hintText: s.captureNoteHint,
                    prefixIcon: const Icon(Icons.edit_note_outlined),
                  ),
                ),
                const SizedBox(height: 16),
                Row(
                  children: [
                    Expanded(
                      child: OutlinedButton.icon(
                        onPressed: () => Navigator.of(ctx).pop('remove'),
                        icon: const Icon(Icons.delete_outline),
                        label: Text(s.captureRemove),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: FilledButton(
                        onPressed: () => Navigator.of(ctx).pop('save'),
                        child: Text(s.captureSave),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          );
        },
      ),
    );
    final noteText = noteCtrl.text.trim();
    noteCtrl.dispose();
    if (!mounted || result == null) return;
    if (result == 'remove') return _remove(it);
    if (qty != it.quantity) await _setQty(it, qty);
    final newNote = noteText.isEmpty ? null : noteText;
    if (newNote != it.note) await _setNote(it, newNote);
    if (course != it.course) await _setCourse(it, course);
  }

  Future<void> _setCourse(OrderItem it, Course course) async {
    try {
      await _ctrl.setCourse(it.id, course);
    } on ApiError catch (e) {
      _toast(e.message);
    }
  }

  Future<void> _setNote(OrderItem it, String? note) async {
    try {
      await _ctrl.setNote(it.id, note);
    } on ApiError catch (e) {
      _toast(e.message);
    }
  }

  // --- Barra de acción fija (zona del pulgar) ---

  Widget _actionBar(BuildContext context, Strings s, Order order) {
    final scheme = Theme.of(context).colorScheme;
    final ready = order.readyCount;
    final pending = order.pendingCount;
    return Container(
      padding: const EdgeInsets.fromLTRB(16, 10, 16, 10),
      decoration: BoxDecoration(
        color: scheme.surface.withValues(alpha: 0.75),
        border: Border(
          top: BorderSide(color: scheme.outlineVariant.withValues(alpha: 0.5)),
        ),
      ),
      child: Row(
        children: [
          // Hay platos listos: servir es lo primario (ámbar de atención).
          if (ready > 0) ...[
            Expanded(
              child: FilledButton.icon(
                style: FilledButton.styleFrom(
                  backgroundColor: WellnodPalette.warn,
                  foregroundColor: Colors.black,
                  minimumSize: const Size(0, 48),
                ),
                onPressed: _serve,
                icon: const Icon(Icons.room_service_outlined),
                label: Text(s.markServedCount(ready)),
              ),
            ),
            const SizedBox(width: 8),
          ],
          // Se está cargando: marchar. Sin pendientes pero con un curso en
          // espera: "Marchar principales". Sin nada: marchar deshabilitado.
          if (pending > 0) ...[
            Expanded(
              child: FilledButton.icon(
                style: FilledButton.styleFrom(minimumSize: const Size(0, 48)),
                onPressed: _march,
                icon: const Icon(Icons.send),
                label: Text(s.marchCount(pending)),
              ),
            ),
            const SizedBox(width: 8),
          ] else if (order.nextCourse != null) ...[
            Expanded(
              child: FilledButton.icon(
                style: FilledButton.styleFrom(minimumSize: const Size(0, 48)),
                onPressed: _fireNext,
                icon: const Icon(Icons.send),
                label: Text(s.fireCourse(order.nextCourse!)),
              ),
            ),
            const SizedBox(width: 8),
          ] else if (ready == 0) ...[
            Expanded(
              child: FilledButton.icon(
                style: FilledButton.styleFrom(minimumSize: const Size(0, 48)),
                onPressed: null,
                icon: const Icon(Icons.send),
                label: Text(s.marchCount(0)),
              ),
            ),
            const SizedBox(width: 8),
          ],
          IconButton.outlined(
            onPressed: _openCobro,
            icon: const Icon(Icons.payments_outlined),
            tooltip: s.cobro,
            style: IconButton.styleFrom(minimumSize: const Size(48, 48)),
          ),
        ],
      ),
    );
  }

  // --- Acciones ---

  OrderController get _ctrl =>
      ref.read(orderControllerProvider(orderId).notifier);

  Future<void> _claim(Strings s) async {
    final messenger = ScaffoldMessenger.of(context);
    try {
      await ref.read(orderRepositoryProvider).claim(orderId);
      ref.invalidate(orderControllerProvider(orderId));
      ref.read(floorProvider.notifier).refresh();
      messenger.showSnackBar(SnackBar(content: Text(s.claimDone)));
    } on ApiError catch (e) {
      messenger.showSnackBar(SnackBar(content: Text(e.message)));
    }
  }

  void _openCobro() {
    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (_) => SizedBox(
        height: MediaQuery.of(context).size.height * 0.85,
        child: CobroSheet(orderId: orderId),
      ),
    );
  }

  /// Tap en la grilla: +1 directo (el haptic lo dispara la grilla). Si el
  /// producto tiene un grupo obligatorio (punto del bife), primero hay que
  /// elegir: sheet rápido — con un único grupo de elegir-uno, el chip agrega.
  Future<void> _add(Product p) async {
    if (p.needsChoice) {
      final r = await showItemOptionsSheet(context, p, quick: true);
      if (r == null || !mounted) return;
      return _addResolved(p, r);
    }
    try {
      await _ctrl.addProduct(p, 1);
    } on ApiError catch (e) {
      _toast(e.message);
    }
  }

  /// Mantener presionado: todos los modificadores + cantidad + nota.
  Future<void> _addWithOptions(Product p) async {
    final r = await showItemOptionsSheet(context, p, quick: false);
    if (r == null || !mounted) return;
    return _addResolved(p, r);
  }

  Future<void> _addResolved(Product p, ItemOptions r) async {
    try {
      await _ctrl.addProduct(p, r.qty, note: r.note, optionIds: r.optionIds);
    } on ApiError catch (e) {
      _toast(e.message);
    }
  }

  Future<void> _setQty(OrderItem it, int qty) async {
    if (qty < 1) return _remove(it);
    try {
      await _ctrl.setQty(it.id, qty);
    } on ApiError catch (e) {
      _toast(e.message);
    }
  }

  Future<void> _remove(OrderItem it) async {
    try {
      await _ctrl.removeItem(it.id);
    } on ApiError catch (e) {
      _toast(e.message);
    }
  }

  Future<void> _serve() async {
    final s = context.s;
    final messenger = ScaffoldMessenger.of(context);
    try {
      HapticFeedback.mediumImpact();
      await _ctrl.served();
      if (!mounted) return;
      ref.read(floorProvider.notifier).refresh();
      messenger.showSnackBar(SnackBar(content: Text(s.readyServedDone)));
    } on ApiError catch (e) {
      _toast(e.message);
    }
  }

  Future<void> _fireNext() async {
    try {
      HapticFeedback.mediumImpact();
      await _ctrl.fireNext();
      if (mounted) ref.read(floorProvider.notifier).refresh();
    } on ApiError catch (e) {
      _toast(e.message);
    }
  }

  Future<void> _fireAll() async {
    try {
      HapticFeedback.mediumImpact();
      await _ctrl.fireAll();
      if (mounted) ref.read(floorProvider.notifier).refresh();
    } on ApiError catch (e) {
      _toast(e.message);
    }
  }

  Future<void> _serveCourse(Course c) async {
    final done = context.s.readyServedDone;
    try {
      await _ctrl.serveCourse(c);
      if (!mounted) return;
      ref.read(floorProvider.notifier).refresh();
      _toast(done);
    } on ApiError catch (e) {
      _toast(e.message);
    }
  }

  Future<void> _march() async {
    try {
      HapticFeedback.mediumImpact();
      await _ctrl.send();
      await _printTicket(); // best-effort: si no hay impresora, no bloquea
      if (!mounted) return;
      ref.read(floorProvider.notifier).refresh();
      Navigator.of(context).pop();
    } on ApiError catch (e) {
      _toast(e.message);
    }
  }

  Future<void> _printTicket() async {
    final order = ref.read(orderControllerProvider(orderId)).valueOrNull;
    if (order == null) return;
    String? label;
    final tables = ref.read(floorProvider).valueOrNull ?? const <FloorTable>[];
    for (final t in tables) {
      if (t.id == order.tableId) {
        label = t.name ?? context.s.tableLabel(t.number);
        break;
      }
    }
    final bytes = await buildKitchenTicket(order, tableLabel: label);
    await ref.read(printerServiceProvider).printBytes(bytes);
  }

  Future<void> _moveToFree() async {
    final s = context.s;
    final tables = ref.read(floorProvider).valueOrNull ?? const <FloorTable>[];
    final free = tables.where((t) => t.isFree).toList();
    final picked = await _pickTable(free, s.moveTable, s.noFreeTables);
    if (picked == null) return;
    try {
      await _ctrl.transfer(picked.id);
      if (!mounted) return;
      ref.read(floorProvider.notifier).refresh();
      Navigator.of(context).pop();
    } on ApiError catch (e) {
      _toast(e.message);
    }
  }

  Future<void> _mergeHere() async {
    final s = context.s;
    final tables = ref.read(floorProvider).valueOrNull ?? const <FloorTable>[];
    final others = tables
        .where((t) => t.activeOrder != null && t.activeOrder!.id != orderId)
        .toList();
    final picked = await _pickTable(others, s.mergeTable, s.noOtherTables);
    if (picked?.activeOrder == null) return;
    try {
      await _ctrl.merge(picked!.activeOrder!.id);
      if (mounted) ref.read(floorProvider.notifier).refresh();
    } on ApiError catch (e) {
      _toast(e.message);
    }
  }

  Future<FloorTable?> _pickTable(
    List<FloorTable> tables,
    String title,
    String emptyMsg,
  ) {
    final s = context.s;
    return showModalBottomSheet<FloorTable>(
      context: context,
      builder: (_) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Padding(
              padding: const EdgeInsets.all(16),
              child: Text(
                title,
                style: Theme.of(context).textTheme.titleMedium,
              ),
            ),
            if (tables.isEmpty)
              Padding(padding: const EdgeInsets.all(16), child: Text(emptyMsg))
            else
              Flexible(
                child: ListView(
                  shrinkWrap: true,
                  children: [
                    for (final t in tables)
                      ListTile(
                        title: Text(t.name ?? s.tableLabel(t.number)),
                        onTap: () => Navigator.of(context).pop(t),
                      ),
                  ],
                ),
              ),
            const SizedBox(height: 8),
          ],
        ),
      ),
    );
  }

  void _toast(String message) {
    if (!mounted) return;
    ScaffoldMessenger.of(context)
        .showSnackBar(SnackBar(content: Text(message)));
  }
}
