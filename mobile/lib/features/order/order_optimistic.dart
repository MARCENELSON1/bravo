import 'order_dtos.dart';
import 'product_dtos.dart';

/// Transformaciones optimistas puras sobre una `Order` (para feedback instantáneo
/// antes de que responda el server). Solo tocan ítems PENDING; el server manda.

Order applyAdd(Order o, Product p, int qty, String itemId, {String? note}) {
  final item = OrderItem(
    id: itemId,
    productId: p.id,
    name: p.name,
    unitPriceAmount: p.priceAmount,
    quantity: qty,
    status: ItemStatus.pending,
    station: Station.fromApi(p.station),
    note: note,
  );
  return o.copyWith(
    items: [...o.items, item],
    totalAmount: o.totalAmount + p.priceAmount * qty,
  );
}

Order applyQty(Order o, String itemId, int qty) {
  var delta = 0;
  final items = o.items.map((i) {
    if (i.id == itemId && i.status.isPending) {
      delta += (qty - i.quantity) * i.unitPriceAmount;
      return i.copyWith(quantity: qty);
    }
    return i;
  }).toList();
  return o.copyWith(items: items, totalAmount: o.totalAmount + delta);
}

Order applyNote(Order o, String itemId, String? note) {
  final items = o.items
      .map((i) => i.id == itemId && i.status.isPending ? i.copyWith(note: note) : i)
      .toList();
  return o.copyWith(items: items);
}

Order applyRemove(Order o, String itemId) {
  final delta = o.items
      .where((i) => i.id == itemId && i.status.isPending)
      .fold(0, (a, i) => a + i.lineTotal);
  return o.copyWith(
    items: o.items.where((i) => i.id != itemId).toList(),
    totalAmount: o.totalAmount - delta,
  );
}
