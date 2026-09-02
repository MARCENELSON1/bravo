// DTO de producto contra ProductResponse (openapi.json).
class Product {
  const Product({
    required this.id,
    required this.name,
    required this.priceAmount,
    required this.currency,
    required this.station,
    required this.active,
    this.category,
    this.imageUrl,
    this.description,
    this.availableToday = true,
  });

  final String id;
  final String name;
  final int priceAmount;
  final String currency;
  final String station; // KITCHEN | BAR
  final bool active;
  final String? category;
  final String? imageUrl;
  final String? description;
  final bool availableToday;

  /// Se puede pedir hoy (activo y no "86'd").
  bool get orderable => active && availableToday;

  factory Product.fromJson(Map<String, dynamic> j) => Product(
        id: j['id'] as String,
        name: j['name'] as String,
        priceAmount: j['price_amount'] as int,
        currency: j['currency'] as String,
        station: j['station'] as String,
        active: j['active'] as bool? ?? true,
        category: j['category'] as String?,
        imageUrl: j['image_url'] as String?,
        description: j['description'] as String?,
        availableToday: j['available_today'] as bool? ?? true,
      );
}
