import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/api_client.dart';
import '../../api/dio_errors.dart';

/// Proveedor (backend `SupplierResponse`).
class Supplier {
  const Supplier({
    required this.id,
    required this.name,
    required this.active,
    this.contact,
    this.phone,
    this.notes,
  });

  final String id;
  final String name;
  final bool active;
  final String? contact;
  final String? phone;
  final String? notes;

  factory Supplier.fromJson(Map<String, dynamic> j) => Supplier(
        id: j['id'] as String,
        name: j['name'] as String,
        active: (j['active'] as bool?) ?? true,
        contact: j['contact'] as String?,
        phone: j['phone'] as String?,
        notes: j['notes'] as String?,
      );
}

class SupplierRepository {
  SupplierRepository(this._dio);

  final Dio _dio;

  Future<List<Supplier>> list() async {
    try {
      final res = await _dio.get<dynamic>('/inventory/suppliers');
      return (res.data as List)
          .map((e) => Supplier.fromJson(Map<String, dynamic>.from(e as Map)))
          .toList();
    } catch (e) {
      throw toApiError(e);
    }
  }

  Future<void> create({
    required String name,
    String? contact,
    String? phone,
    String? notes,
  }) async {
    try {
      await _dio.post<dynamic>('/inventory/suppliers', data: {
        'name': name,
        'contact': ?contact,
        'phone': ?phone,
        'notes': ?notes,
      });
    } catch (e) {
      throw toApiError(e);
    }
  }

  Future<void> update(
    String supplierId, {
    required String name,
    String? contact,
    String? phone,
    String? notes,
    required bool active,
  }) async {
    try {
      await _dio.put<dynamic>('/inventory/suppliers/$supplierId', data: {
        'name': name,
        'contact': ?contact,
        'phone': ?phone,
        'notes': ?notes,
        'active': active,
      });
    } catch (e) {
      throw toApiError(e);
    }
  }
}

final supplierRepositoryProvider = Provider<SupplierRepository>(
  (ref) => SupplierRepository(ref.read(apiDioProvider)),
);

final suppliersProvider = FutureProvider.autoDispose<List<Supplier>>(
  (ref) => ref.read(supplierRepositoryProvider).list(),
);
