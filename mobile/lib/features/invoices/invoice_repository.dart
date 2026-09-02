import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/api_client.dart';
import '../../api/dio_errors.dart';

/// Comprobante fiscal (backend `InvoiceResponse`).
class Invoice {
  const Invoice({
    required this.id,
    required this.type,
    required this.docType,
    required this.status,
    required this.net,
    required this.vat,
    required this.total,
    required this.currency,
    this.number,
    this.pointOfSale,
    this.cae,
  });

  final String id;
  final String type;
  final String docType;
  final String status;
  final int net;
  final int vat;
  final int total;
  final String currency;
  final int? number;
  final int? pointOfSale;
  final String? cae;

  factory Invoice.fromJson(Map<String, dynamic> j) => Invoice(
        id: j['id'] as String,
        type: j['type'] as String,
        docType: j['doc_type'] as String,
        status: j['status'] as String,
        net: (j['net'] as int?) ?? 0,
        vat: (j['vat'] as int?) ?? 0,
        total: (j['total'] as int?) ?? 0,
        currency: j['currency'] as String,
        number: j['number'] as int?,
        pointOfSale: j['point_of_sale'] as int?,
        cae: j['cae'] as String?,
      );
}

enum DocType {
  cuit,
  cuil,
  dni,
  consumidorFinal;

  String get api => switch (this) {
        DocType.cuit => 'CUIT',
        DocType.cuil => 'CUIL',
        DocType.dni => 'DNI',
        DocType.consumidorFinal => 'CONSUMIDOR_FINAL',
      };
}

class InvoiceRepository {
  InvoiceRepository(this._dio);

  final Dio _dio;

  Future<List<Invoice>> list() async {
    try {
      final res = await _dio.get<dynamic>('/invoices');
      return (res.data as List)
          .map((e) => Invoice.fromJson(Map<String, dynamic>.from(e as Map)))
          .toList();
    } catch (e) {
      throw toApiError(e);
    }
  }

  /// Comprobante ya emitido para una orden, o null si no hay.
  Future<Invoice?> forOrder(String orderId) async {
    try {
      final res = await _dio.get<dynamic>('/orders/$orderId/invoice');
      if (res.data is! Map) return null;
      return Invoice.fromJson(Map<String, dynamic>.from(res.data as Map));
    } on DioException catch (e) {
      final code = e.response?.statusCode;
      if (code == 404 || code == 422) return null;
      throw toApiError(e);
    } catch (e) {
      throw toApiError(e);
    }
  }

  /// Emite el comprobante fiscal de la orden (AFIP → CAE).
  Future<Invoice> issueForOrder(
    String orderId, {
    required DocType docType,
    String? docNumber,
  }) async {
    try {
      final res = await _dio.post<dynamic>(
        '/orders/$orderId/invoice',
        data: {'doc_type': docType.api, 'doc_number': ?docNumber},
      );
      return Invoice.fromJson(Map<String, dynamic>.from(res.data as Map));
    } catch (e) {
      throw toApiError(e);
    }
  }
}

final invoiceRepositoryProvider = Provider<InvoiceRepository>(
  (ref) => InvoiceRepository(ref.read(apiDioProvider)),
);

final invoicesProvider = FutureProvider.autoDispose<List<Invoice>>(
  (ref) => ref.read(invoiceRepositoryProvider).list(),
);

final orderInvoiceProvider =
    FutureProvider.autoDispose.family<Invoice?, String>(
  (ref, orderId) => ref.read(invoiceRepositoryProvider).forOrder(orderId),
);
