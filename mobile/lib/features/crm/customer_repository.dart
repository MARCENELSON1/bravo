import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/api_client.dart';
import '../../api/dio_errors.dart';

/// Cliente CRM (backend `CustomerResponse`).
class Customer {
  const Customer({
    required this.id,
    required this.name,
    required this.noContactar,
    this.phone,
    this.email,
    this.notes,
  });

  final String id;
  final String name;
  final bool noContactar;
  final String? phone;
  final String? email;
  final String? notes;

  factory Customer.fromJson(Map<String, dynamic> j) => Customer(
        id: j['id'] as String,
        name: j['name'] as String,
        noContactar: (j['no_contactar'] as bool?) ?? false,
        phone: j['phone'] as String?,
        email: j['email'] as String?,
        notes: j['notes'] as String?,
      );
}

class CustomerRepository {
  CustomerRepository(this._dio);

  final Dio _dio;

  Future<List<Customer>> list() async {
    try {
      final res = await _dio.get<dynamic>('/customers');
      return (res.data as List)
          .map((e) => Customer.fromJson(Map<String, dynamic>.from(e as Map)))
          .toList();
    } catch (e) {
      throw toApiError(e);
    }
  }

  Map<String, dynamic> _body({
    required String name,
    String? phone,
    String? email,
    String? notes,
    required bool noContactar,
  }) =>
      {
        'name': name,
        'phone': ?phone,
        'email': ?email,
        'notes': ?notes,
        'no_contactar': noContactar,
      };

  Future<void> create({
    required String name,
    String? phone,
    String? email,
    String? notes,
    bool noContactar = false,
  }) async {
    try {
      await _dio.post<dynamic>('/customers',
          data: _body(
              name: name,
              phone: phone,
              email: email,
              notes: notes,
              noContactar: noContactar));
    } catch (e) {
      throw toApiError(e);
    }
  }

  Future<void> update(
    String customerId, {
    required String name,
    String? phone,
    String? email,
    String? notes,
    required bool noContactar,
  }) async {
    try {
      await _dio.put<dynamic>('/customers/$customerId',
          data: _body(
              name: name,
              phone: phone,
              email: email,
              notes: notes,
              noContactar: noContactar));
    } catch (e) {
      throw toApiError(e);
    }
  }
}

final customerRepositoryProvider = Provider<CustomerRepository>(
  (ref) => CustomerRepository(ref.read(apiDioProvider)),
);

final customersProvider = FutureProvider.autoDispose<List<Customer>>(
  (ref) => ref.read(customerRepositoryProvider).list(),
);
