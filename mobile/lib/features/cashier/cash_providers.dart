import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/api_client.dart';
import 'cash_dtos.dart';
import 'cash_repository.dart';
import 'payment_dtos.dart';
import 'payment_repository.dart';

final cashRepositoryProvider = Provider<CashRepository>(
  (ref) => CashRepository(ref.read(apiDioProvider)),
);

final paymentRepositoryProvider = Provider<PaymentRepository>(
  (ref) => PaymentRepository(ref.read(apiDioProvider)),
);

/// Sesión de caja actual (null si no hay una abierta).
final currentCashSessionProvider = FutureProvider.autoDispose<CashSession?>(
  (ref) => ref.read(cashRepositoryProvider).current(),
);

/// Pagos de una orden (para el cobro).
final orderPaymentsProvider =
    FutureProvider.autoDispose.family<List<Payment>, String>(
  (ref, orderId) => ref.read(paymentRepositoryProvider).list(orderId),
);
