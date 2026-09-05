// DTO de producto contra ProductResponse (openapi.json) + sus grupos de
// modificadores (ProductModifiersResponse, precargados en batch por el repo).

/// Una opción de un grupo ("Jugoso", "+Panceta"). `priceDelta` en unidades
/// menores, se pliega en el precio del ítem al agregar (el server manda).
class ModifierOption {
  const ModifierOption({
    required this.id,
    required this.name,
    this.priceDelta = 0,
  });

  final String id;
  final String name;
  final int priceDelta;

  factory ModifierOption.fromJson(Map<String, dynamic> j) => ModifierOption(
    id: j['id'] as String,
    name: j['name'] as String,
    priceDelta: j['price_delta'] as int? ?? 0,
  );
}

/// Un grupo ("Punto de cocción", "Agregados"): `minSelect`/`maxSelect` son la
/// regla (1/1 = elegir exactamente uno; 0/3 = hasta tres, opcional).
class ModifierGroup {
  const ModifierGroup({
    required this.id,
    required this.name,
    required this.minSelect,
    required this.maxSelect,
    required this.options,
  });

  final String id;
  final String name;
  final int minSelect;
  final int maxSelect;
  final List<ModifierOption> options;

  bool get required => minSelect >= 1;
  bool get single => maxSelect == 1;

  factory ModifierGroup.fromJson(Map<String, dynamic> j) => ModifierGroup(
    id: j['id'] as String,
    name: j['name'] as String,
    minSelect: j['min_select'] as int? ?? 0,
    maxSelect: j['max_select'] as int? ?? 1,
    options: ((j['options'] as List?) ?? const [])
        .map(
          (e) => ModifierOption.fromJson(Map<String, dynamic>.from(e as Map)),
        )
        .toList(),
  );
}

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
    this.modifierGroups = const [],
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
  final List<ModifierGroup> modifierGroups;

  /// Se puede pedir hoy (activo y no "86'd").
  bool get orderable => active && availableToday;

  /// Tiene al menos un grupo obligatorio ("punto del bife"): al tocarlo hay que
  /// elegir antes de agregar.
  bool get needsChoice => modifierGroups.any((g) => g.required);

  Product withModifierGroups(List<ModifierGroup> groups) => Product(
    id: id,
    name: name,
    priceAmount: priceAmount,
    currency: currency,
    station: station,
    active: active,
    category: category,
    imageUrl: imageUrl,
    description: description,
    availableToday: availableToday,
    modifierGroups: groups,
  );

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
