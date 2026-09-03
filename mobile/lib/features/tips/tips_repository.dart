import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/api_client.dart';
import '../../api/dio_errors.dart';
import '../cashier/payment_dtos.dart';
import 'tips_dtos.dart';

class TipsRepository {
  TipsRepository(this._dio);

  final Dio _dio;

  Future<TipsReport> report() async {
    try {
      final res = await _dio.get<dynamic>('/cashier/tips/report');
      return TipsReport.fromJson(Map<String, dynamic>.from(res.data as Map));
    } catch (e) {
      throw toApiError(e);
    }
  }

  Future<void> payout({
    required String waiterId,
    required int amount,
    required PaymentMethod method,
  }) async {
    try {
      await _dio.post<dynamic>(
        '/cashier/tips/payout',
        data: {'waiter_id': waiterId, 'amount': amount, 'method': method.api},
      );
    } catch (e) {
      throw toApiError(e);
    }
  }
}

final tipsRepositoryProvider = Provider<TipsRepository>(
  (ref) => TipsRepository(ref.read(apiDioProvider)),
);

final tipsReportProvider = FutureProvider.autoDispose<TipsReport>(
  (ref) => ref.read(tipsRepositoryProvider).report(),
);
