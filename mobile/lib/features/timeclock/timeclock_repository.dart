import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/api_client.dart';
import '../../api/dio_errors.dart';
import 'timeclock_dtos.dart';

class TimeclockRepository {
  TimeclockRepository(this._dio);

  final Dio _dio;

  Future<MyTimeclock> me() async {
    try {
      final res = await _dio.get<dynamic>('/timeclock/me');
      return MyTimeclock.fromJson(Map<String, dynamic>.from(res.data as Map));
    } catch (e) {
      throw toApiError(e);
    }
  }

  Future<Shift> clockIn({String? note}) async {
    try {
      final res = await _dio.post<dynamic>('/timeclock/clock-in', data: {'note': ?note});
      return Shift.fromJson(Map<String, dynamic>.from(res.data as Map));
    } catch (e) {
      throw toApiError(e);
    }
  }

  Future<Shift> clockOut() async {
    try {
      final res = await _dio.post<dynamic>('/timeclock/clock-out');
      return Shift.fromJson(Map<String, dynamic>.from(res.data as Map));
    } catch (e) {
      throw toApiError(e);
    }
  }
}

final timeclockRepositoryProvider = Provider<TimeclockRepository>(
  (ref) => TimeclockRepository(ref.read(apiDioProvider)),
);

final myTimeclockProvider = FutureProvider.autoDispose<MyTimeclock>(
  (ref) => ref.read(timeclockRepositoryProvider).me(),
);
