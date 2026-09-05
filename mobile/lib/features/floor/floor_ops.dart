import 'floor_dtos.dart';
import 'floor_view.dart';

/// Lógica pura del plano (sin widgets): urgencia, resumen del mozo y
/// transiciones a "atención" (para el pulso visual).

/// Las mesas que piden atención (para servir / a cobrar) van primero, la que
/// más espera arriba; el resto conserva el orden de la carta de mesas. Así la
/// mesa que lleva 18′ esperando "grita" en vez de esconderse por número.
List<FloorTable> sortByUrgency(List<FloorTable> tables, {DateTime? now}) {
  final indexed = tables.asMap().entries.toList();
  int rank(FloorTable t) => floorView(t, now: now).attention ? 0 : 1;
  int minutes(FloorTable t) => floorView(t, now: now).minutes ?? -1;
  indexed.sort((a, b) {
    final byRank = rank(a.value).compareTo(rank(b.value));
    if (byRank != 0) return byRank;
    if (rank(a.value) == 0) {
      final byWait = minutes(b.value).compareTo(minutes(a.value));
      if (byWait != 0) return byWait;
    }
    return a.key.compareTo(b.key);
  });
  return indexed.map((e) => e.value).toList();
}

/// Foco del mozo de un vistazo: cuántas mesas son suyas, cuántas piden servir
/// (en todo el piso: el que ve, sirve), y cuánto llevan sus mesas.
class FloorSummary {
  const FloorSummary({
    required this.mine,
    required this.toServe,
    required this.toCharge,
    required this.mineTotal,
  });

  final int mine;
  final int toServe;
  final int toCharge;
  final int mineTotal;
}

FloorSummary summarizeFloor(
  List<FloorTable> tables,
  String? userId, {
  DateTime? now,
}) {
  var mine = 0, toServe = 0, toCharge = 0, mineTotal = 0;
  for (final t in tables) {
    final v = floorView(t, now: now);
    if (v.status == FloorStatus.toServe) toServe++;
    if (v.status == FloorStatus.toCharge) toCharge++;
    if (userId != null && t.session?.waiterId == userId) {
      mine++;
      mineTotal += t.activeOrder?.totalAmount ?? 0;
    }
  }
  return FloorSummary(
    mine: mine,
    toServe: toServe,
    toCharge: toCharge,
    mineTotal: mineTotal,
  );
}

/// Ids de las mesas que en este refresco PASARON a pedir atención (antes no
/// pedían, o no existían). Alimenta el pulso: se nota lo nuevo, no lo viejo.
Set<String> newlyAttention(
  Map<String, bool> previousAttention,
  List<FloorTable> tables, {
  DateTime? now,
}) {
  final out = <String>{};
  for (final t in tables) {
    final nowAttention = floorView(t, now: now).attention;
    if (nowAttention && previousAttention[t.id] != true) out.add(t.id);
  }
  return out;
}

/// Snapshot de atención por mesa, para comparar en el próximo refresco.
Map<String, bool> attentionSnapshot(List<FloorTable> tables, {DateTime? now}) =>
    {for (final t in tables) t.id: floorView(t, now: now).attention};
