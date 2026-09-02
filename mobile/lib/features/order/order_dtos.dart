// DTOs de orden/ítem hechos a mano contra los schemas reales de la API
// (OrderResponse / OrderItemResponse / SelectedOptionResponse de openapi.json).
// El precio y el total los calcula el server; acá solo se muestran.

/// Ciclo del ítem (backend `ItemStatus`).
enum ItemStatus {
  pending,
  sent,
  preparing,
  ready,
  served,
  cancelled;

  static ItemStatus fromApi(String v) => switch (v) {
        'PENDING' => ItemStatus.pending,
        'SENT' => ItemStatus.sent,
        'PREPARING' => ItemStatus.preparing,
        'READY' => ItemStatus.ready,
        'SERVED' => ItemStatus.served,
        'CANCELLED' => ItemStatus.cancelled,
        _ => ItemStatus.pending,
      };

  bool get isPending => this == ItemStatus.pending;
  bool get isCancelled => this == ItemStatus.cancelled;
}

/// Estación de despacho (backend `Station`).
enum Station {
  kitchen,
  bar;

  static Station fromApi(String v) => v == 'BAR' ? Station.bar : Station.kitchen;
}

class SelectedOption {
  const SelectedOption({
    required this.optionId,
    required this.name,
    required this.priceDelta,
  });

  final String optionId;
  final String name;
  final int priceDelta;

  factory SelectedOption.fromJson(Map<String, dynamic> j) => SelectedOption(
        optionId: j['option_id'] as String,
        name: j['name'] as String,
        priceDelta: j['price_delta'] as int,
      );
}

class OrderItem {
  const OrderItem({
    required this.id,
    required this.productId,
    required this.name,
    required this.unitPriceAmount,
    required this.quantity,
    required this.status,
    required this.station,
    this.note,
    this.sentAt,
    this.selectedOptions = const [],
  });

  final String id;
  final String productId;
  final String name;
  final int unitPriceAmount;
  final int quantity;
  final ItemStatus status;
  final Station station;
  final String? note;
  final DateTime? sentAt;
  final List<SelectedOption> selectedOptions;

  int get lineTotal => unitPriceAmount * quantity;

  OrderItem copyWith({int? quantity}) => OrderItem(
        id: id,
        productId: productId,
        name: name,
        unitPriceAmount: unitPriceAmount,
        quantity: quantity ?? this.quantity,
        status: status,
        station: station,
        note: note,
        sentAt: sentAt,
        selectedOptions: selectedOptions,
      );

  factory OrderItem.fromJson(Map<String, dynamic> j) => OrderItem(
        id: j['id'] as String,
        productId: j['product_id'] as String,
        name: j['name'] as String,
        unitPriceAmount: j['unit_price_amount'] as int,
        quantity: j['quantity'] as int,
        status: ItemStatus.fromApi(j['status'] as String),
        station: Station.fromApi(j['station'] as String),
        note: j['note'] as String?,
        sentAt: _parseDate(j['sent_at']),
        selectedOptions: ((j['selected_options'] as List?) ?? const [])
            .map((e) => SelectedOption.fromJson(Map<String, dynamic>.from(e as Map)))
            .toList(),
      );
}

class Order {
  const Order({
    required this.id,
    required this.tableId,
    required this.status,
    required this.currency,
    required this.items,
    required this.totalAmount,
    this.createdAt,
  });

  final String id;
  final String tableId;
  final String status;
  final String currency;
  final List<OrderItem> items;
  final int totalAmount;
  final DateTime? createdAt;

  /// Ítems vivos (sin cancelados) — para contar líneas de la comanda.
  List<OrderItem> get liveItems =>
      items.where((i) => !i.status.isCancelled).toList();

  int get pendingCount =>
      items.where((i) => i.status.isPending).fold(0, (a, i) => a + i.quantity);

  Order copyWith({List<OrderItem>? items, int? totalAmount}) => Order(
        id: id,
        tableId: tableId,
        status: status,
        currency: currency,
        items: items ?? this.items,
        totalAmount: totalAmount ?? this.totalAmount,
        createdAt: createdAt,
      );

  factory Order.fromJson(Map<String, dynamic> j) => Order(
        id: j['id'] as String,
        tableId: j['table_id'] as String,
        status: j['status'] as String,
        currency: j['currency'] as String,
        items: ((j['items'] as List?) ?? const [])
            .map((e) => OrderItem.fromJson(Map<String, dynamic>.from(e as Map)))
            .toList(),
        totalAmount: j['total_amount'] as int,
        createdAt: _parseDate(j['created_at']),
      );
}

DateTime? _parseDate(Object? v) =>
    v is String ? DateTime.tryParse(v)?.toLocal() : null;
