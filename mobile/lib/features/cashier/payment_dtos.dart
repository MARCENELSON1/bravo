/// Métodos de pago (backend `PaymentMethod`).
enum PaymentMethod {
  cash,
  card,
  transfer,
  mercadopago,
  qr;

  String get api => switch (this) {
        PaymentMethod.cash => 'CASH',
        PaymentMethod.card => 'CARD',
        PaymentMethod.transfer => 'TRANSFER',
        PaymentMethod.mercadopago => 'MERCADOPAGO',
        PaymentMethod.qr => 'QR',
      };

  static PaymentMethod fromApi(String v) => switch (v) {
        'CASH' => PaymentMethod.cash,
        'CARD' => PaymentMethod.card,
        'TRANSFER' => PaymentMethod.transfer,
        'MERCADOPAGO' => PaymentMethod.mercadopago,
        'QR' => PaymentMethod.qr,
        _ => PaymentMethod.cash,
      };
}

/// Un pago registrado (backend `PaymentResponse`).
class Payment {
  const Payment({
    required this.id,
    required this.method,
    required this.amount,
    required this.tipAmount,
    required this.status,
    required this.direction,
    required this.currency,
    this.checkoutUrl,
  });

  final String id;
  final PaymentMethod method;
  final int amount;
  final int tipAmount;
  final String status; // PENDING | CONFIRMED | REFUNDED ...
  final String direction; // INFLOW | OUTFLOW
  final String currency;
  final String? checkoutUrl;

  bool get isConfirmedInflow => status == 'CONFIRMED' && direction == 'INFLOW';
  bool get isRefundable => status == 'CONFIRMED' && direction == 'INFLOW';

  factory Payment.fromJson(Map<String, dynamic> j) => Payment(
        id: j['id'] as String,
        method: PaymentMethod.fromApi(j['method'] as String),
        amount: j['amount'] as int,
        tipAmount: (j['tip_amount'] as int?) ?? 0,
        status: j['status'] as String,
        direction: j['direction'] as String,
        currency: j['currency'] as String,
        checkoutUrl: j['checkout_url'] as String?,
      );
}
