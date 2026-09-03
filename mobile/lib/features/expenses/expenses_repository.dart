import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/api_client.dart';
import '../../api/dio_errors.dart';

/// Un gasto (egreso) — backend `PaymentResponse` con `direction=OUTFLOW`.
class Expense {
  const Expense({
    required this.id,
    required this.method,
    required this.amount,
    required this.currency,
    this.category,
    this.counterparty,
    this.description,
  });

  final String id;
  final String method;
  final int amount;
  final String currency;
  final String? category;
  final String? counterparty;
  final String? description;

  factory Expense.fromJson(Map<String, dynamic> j) => Expense(
        id: j['id'] as String,
        method: (j['method'] as String?) ?? '',
        amount: (j['amount'] as int?) ?? 0,
        currency: (j['currency'] as String?) ?? 'ARS',
        category: j['category'] as String?,
        counterparty: j['counterparty'] as String?,
        description: j['description'] as String?,
      );
}

class ExpensesRepository {
  ExpensesRepository(this._dio);
  final Dio _dio;

  Future<List<Expense>> list() async {
    try {
      final res = await _dio.get<dynamic>('/expenses');
      return ((res.data as List?) ?? const [])
          .map((e) => Expense.fromJson(Map<String, dynamic>.from(e as Map)))
          .toList();
    } catch (e) {
      throw toApiError(e);
    }
  }

  Future<void> register({
    required String method,
    required int amount,
    String? category,
    String? counterparty,
    String? description,
  }) async {
    try {
      await _dio.post<dynamic>('/expenses', data: {
        'method': method,
        'amount': amount,
        'category': category,
        'counterparty': counterparty,
        'description': description,
      });
    } catch (e) {
      throw toApiError(e);
    }
  }
}

final expensesRepositoryProvider = Provider<ExpensesRepository>(
  (ref) => ExpensesRepository(ref.read(apiDioProvider)),
);

final expensesProvider = FutureProvider.autoDispose<List<Expense>>(
  (ref) => ref.read(expensesRepositoryProvider).list(),
);
