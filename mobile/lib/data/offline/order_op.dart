/// Una operación de comanda pendiente de sincronizar (modo contingencia).
/// Todas llevan los UUIDs de cliente → su replay contra el backend es idempotente.
enum OrderOpType { addItem, setQty, setNote, removeItem, send, transfer, merge }

class OrderOp {
  const OrderOp({
    required this.type,
    required this.orderId,
    this.itemId,
    this.productId,
    this.quantity,
    this.note,
    this.tableId,
    this.sourceOrderId,
  });

  final OrderOpType type;
  final String orderId;
  final String? itemId;
  final String? productId;
  final int? quantity;
  final String? note;
  final String? tableId;
  final String? sourceOrderId;

  factory OrderOp.addItem({
    required String orderId,
    required String itemId,
    required String productId,
    required int quantity,
    String? note,
  }) =>
      OrderOp(
        type: OrderOpType.addItem,
        orderId: orderId,
        itemId: itemId,
        productId: productId,
        quantity: quantity,
        note: note,
      );

  factory OrderOp.setNote({
    required String orderId,
    required String itemId,
    String? note,
  }) =>
      OrderOp(
          type: OrderOpType.setNote, orderId: orderId, itemId: itemId, note: note);

  factory OrderOp.setQty({
    required String orderId,
    required String itemId,
    required int quantity,
  }) =>
      OrderOp(
          type: OrderOpType.setQty,
          orderId: orderId,
          itemId: itemId,
          quantity: quantity);

  factory OrderOp.removeItem({required String orderId, required String itemId}) =>
      OrderOp(type: OrderOpType.removeItem, orderId: orderId, itemId: itemId);

  factory OrderOp.send({required String orderId}) =>
      OrderOp(type: OrderOpType.send, orderId: orderId);

  factory OrderOp.transfer({required String orderId, required String tableId}) =>
      OrderOp(type: OrderOpType.transfer, orderId: orderId, tableId: tableId);

  factory OrderOp.merge(
          {required String orderId, required String sourceOrderId}) =>
      OrderOp(
          type: OrderOpType.merge,
          orderId: orderId,
          sourceOrderId: sourceOrderId);

  Map<String, dynamic> toJson() => {
        'type': type.name,
        'orderId': orderId,
        if (itemId != null) 'itemId': itemId,
        if (productId != null) 'productId': productId,
        if (quantity != null) 'quantity': quantity,
        if (note != null) 'note': note,
        if (tableId != null) 'tableId': tableId,
        if (sourceOrderId != null) 'sourceOrderId': sourceOrderId,
      };

  factory OrderOp.fromJson(Map<String, dynamic> j) => OrderOp(
        type: OrderOpType.values.byName(j['type'] as String),
        orderId: j['orderId'] as String,
        itemId: j['itemId'] as String?,
        productId: j['productId'] as String?,
        quantity: j['quantity'] as int?,
        note: j['note'] as String?,
        tableId: j['tableId'] as String?,
        sourceOrderId: j['sourceOrderId'] as String?,
      );
}
