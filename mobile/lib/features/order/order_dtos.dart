// DTOs de orden/ítem hechos a mano contra los schemas reales de la API
// (OrderResponse / OrderItemResponse / SelectedOptionResponse de openapi.json).
// El precio y el total los calcula el server; acá solo se muestran.

/// Ciclo del ítem (backend `ItemStatus`).
enum ItemStatus {
  pending,
  held, // marchado pero en espera de que el mozo dispare su curso
  sent,
  preparing,
  ready,
  served,
  cancelled;

  static ItemStatus fromApi(String v) => switch (v) {
    'PENDING' => ItemStatus.pending,
    'HELD' => ItemStatus.held,
    'SENT' => ItemStatus.sent,
    'PREPARING' => ItemStatus.preparing,
    'READY' => ItemStatus.ready,
    'SERVED' => ItemStatus.served,
    'CANCELLED' => ItemStatus.cancelled,
    _ => ItemStatus.pending,
  };

  bool get isPending => this == ItemStatus.pending;
  bool get isHeld => this == ItemStatus.held;
  bool get isCancelled => this == ItemStatus.cancelled;
  bool get isFired => this == ItemStatus.sent || this == ItemStatus.preparing;
}

/// Tiempo de servicio (backend `Course`). Es del plato (carta); el mozo lo
/// puede cambiar por línea antes de marchar. `immediate` = sin cursos (barra).
enum Course {
  immediate,
  starter,
  main,
  dessert;

  static Course fromApi(String? v) => switch (v) {
    'IMMEDIATE' => Course.immediate,
    'STARTER' => Course.starter,
    'DESSERT' => Course.dessert,
    _ => Course.main,
  };

  String get apiValue => switch (this) {
    Course.immediate => 'IMMEDIATE',
    Course.starter => 'STARTER',
    Course.main => 'MAIN',
    Course.dessert => 'DESSERT',
  };

  /// Orden de servicio (bebidas primero, después entrada → principal → postre).
  int get sequence => index;
  bool get coursed => this != Course.immediate;
}

/// Estado derivado de un curso dentro de la comanda (espeja `CourseState`).
enum CourseState { pending, held, inKitchen, ready, served }

/// Estación de despacho (backend `Station`).
enum Station {
  kitchen,
  bar;

  static Station fromApi(String v) =>
      v == 'BAR' ? Station.bar : Station.kitchen;

  String get apiValue => this == Station.bar ? 'BAR' : 'KITCHEN';
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

const _unset = Object();

class OrderItem {
  const OrderItem({
    required this.id,
    required this.productId,
    required this.name,
    required this.unitPriceAmount,
    required this.quantity,
    required this.status,
    required this.station,
    this.course = Course.main,
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
  final Course course;
  final String? note;
  final DateTime? sentAt;
  final List<SelectedOption> selectedOptions;

  int get lineTotal => unitPriceAmount * quantity;

  /// `note` acepta null para BORRAR la nota (sentinela para distinguir
  /// "no tocar" de "limpiar").
  OrderItem copyWith({int? quantity, Object? note = _unset}) => OrderItem(
    id: id,
    productId: productId,
    name: name,
    unitPriceAmount: unitPriceAmount,
    quantity: quantity ?? this.quantity,
    status: status,
    station: station,
    course: course,
    note: identical(note, _unset) ? this.note : note as String?,
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
    course: Course.fromApi(j['course'] as String?),
    note: j['note'] as String?,
    sentAt: _parseDate(j['sent_at']),
    selectedOptions: ((j['selected_options'] as List?) ?? const [])
        .map(
          (e) => SelectedOption.fromJson(Map<String, dynamic>.from(e as Map)),
        )
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
    this.source = 'WAITER',
    this.createdAt,
    this.activeCourse,
    this.nextCourse,
  });

  final String id;
  final String tableId;
  final String status;
  final String currency;
  final List<OrderItem> items;
  final int totalAmount;
  // Cursos (derivados por el server): el que está al fuego y el próximo en
  // espera ("Marchar principales"). null cuando no aplica.
  final Course? activeCourse;
  final Course? nextCourse;
  // WAITER | CUSTOMER_QR | CUSTOMER_QR_PREPAID (Autoservicio, Fase 3).
  final String source;
  final DateTime? createdAt;

  /// Autoservicio ya pago y servido: la mesa se libera con "Liberar" (no "Cobrar").
  bool get isPrepaidServed =>
      source == 'CUSTOMER_QR_PREPAID' && status == 'SERVED';

  /// Ítems vivos (sin cancelados) — para contar líneas de la comanda.
  List<OrderItem> get liveItems =>
      items.where((i) => !i.status.isCancelled).toList();

  int get pendingCount =>
      items.where((i) => i.status.isPending).fold(0, (a, i) => a + i.quantity);

  /// Ítems ya listos en cocina (READY) esperando que el mozo los marque servidos.
  int get readyCount => items
      .where((i) => i.status == ItemStatus.ready)
      .fold(0, (a, i) => a + i.quantity);

  /// Ítems marchados en espera de que el mozo dispare su curso.
  int get heldCount =>
      items.where((i) => i.status.isHeld).fold(0, (a, i) => a + i.quantity);

  /// Estado del curso (espeja `Order.course_state` del backend). null = sin platos.
  CourseState? courseState(Course c) {
    final st = liveItems
        .where((i) => i.course == c)
        .map((i) => i.status)
        .toSet();
    if (st.isEmpty) return null;
    if (st.contains(ItemStatus.sent) || st.contains(ItemStatus.preparing)) {
      return CourseState.inKitchen;
    }
    if (st.contains(ItemStatus.ready)) return CourseState.ready;
    if (st.contains(ItemStatus.held)) return CourseState.held;
    if (st.contains(ItemStatus.pending)) return CourseState.pending;
    return CourseState.served;
  }

  Order copyWith({List<OrderItem>? items, int? totalAmount}) => Order(
    id: id,
    tableId: tableId,
    status: status,
    currency: currency,
    items: items ?? this.items,
    totalAmount: totalAmount ?? this.totalAmount,
    source: source,
    createdAt: createdAt,
    activeCourse: activeCourse,
    nextCourse: nextCourse,
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
    source: (j['source'] as String?) ?? 'WAITER',
    createdAt: _parseDate(j['created_at']),
    activeCourse: j['active_course'] == null
        ? null
        : Course.fromApi(j['active_course'] as String),
    nextCourse: j['next_course'] == null
        ? null
        : Course.fromApi(j['next_course'] as String),
  );
}

DateTime? _parseDate(Object? v) =>
    v is String ? DateTime.tryParse(v)?.toLocal() : null;
