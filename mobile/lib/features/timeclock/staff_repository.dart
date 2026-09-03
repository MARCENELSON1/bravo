import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/api_client.dart';
import '../../api/dio_errors.dart';
import '../finance/finance_range.dart';

/// Fila del reporte de personal (backend `StaffReportRowResponse`).
class StaffRow {
  const StaffRow({
    required this.userId,
    required this.email,
    required this.workedMinutes,
    required this.overtimeMinutes,
    required this.tablesServed,
    required this.salesAmount,
    required this.currency,
    this.hourlyRateAmount,
  });
  final String userId;
  final String email;
  final int workedMinutes;
  final int overtimeMinutes;
  final int tablesServed;
  final int salesAmount;
  final String currency;
  final int? hourlyRateAmount;
  factory StaffRow.fromJson(Map<String, dynamic> j) => StaffRow(
        userId: j['user_id'] as String,
        email: (j['email'] as String?) ?? '',
        workedMinutes: (j['worked_minutes'] as int?) ?? 0,
        overtimeMinutes: (j['overtime_minutes'] as int?) ?? 0,
        tablesServed: (j['tables_served'] as int?) ?? 0,
        salesAmount: (j['sales_amount'] as int?) ?? 0,
        currency: (j['currency'] as String?) ?? 'ARS',
        hourlyRateAmount: j['hourly_rate_amount'] as int?,
      );
}

class StaffReport {
  const StaffReport({required this.currency, required this.rows});
  final String currency;
  final List<StaffRow> rows;
  factory StaffReport.fromJson(Map<String, dynamic> j) => StaffReport(
        currency: (j['currency'] as String?) ?? 'ARS',
        rows: ((j['rows'] as List?) ?? const [])
            .map((e) => StaffRow.fromJson(Map<String, dynamic>.from(e as Map)))
            .toList(),
      );
}

/// Un turno (backend `ShiftResponse`).
class Shift {
  const Shift({
    required this.id,
    required this.userId,
    required this.clockInAt,
    required this.status,
    required this.source,
    this.clockOutAt,
    this.workedMinutes,
  });
  final String id;
  final String userId;
  final String clockInAt;
  final String status;
  final String source;
  final String? clockOutAt;
  final int? workedMinutes;
  factory Shift.fromJson(Map<String, dynamic> j) => Shift(
        id: j['id'] as String,
        userId: (j['user_id'] as String?) ?? '',
        clockInAt: (j['clock_in_at'] as String?) ?? '',
        status: (j['status'] as String?) ?? '',
        source: (j['source'] as String?) ?? '',
        clockOutAt: j['clock_out_at'] as String?,
        workedMinutes: j['worked_minutes'] as int?,
      );
}

class StaffRepository {
  StaffRepository(this._dio);
  final Dio _dio;

  Map<String, dynamic> _win(RangeWindow w) => {'from': w.from, 'to': w.to};

  Future<StaffReport> report(RangeWindow w) async {
    try {
      final res =
          await _dio.get<dynamic>('/reports/staff', queryParameters: _win(w));
      return StaffReport.fromJson(Map<String, dynamic>.from(res.data as Map));
    } catch (e) {
      throw toApiError(e);
    }
  }

  Future<List<Shift>> shifts(RangeWindow w) async {
    try {
      final res = await _dio.get<dynamic>('/timeclock/shifts',
          queryParameters: _win(w));
      return ((res.data as List?) ?? const [])
          .map((e) => Shift.fromJson(Map<String, dynamic>.from(e as Map)))
          .toList();
    } catch (e) {
      throw toApiError(e);
    }
  }

  Future<void> adjustShift(String shiftId,
      {required String clockInAt, String? clockOutAt}) async {
    try {
      await _dio.patch<dynamic>('/timeclock/shifts/$shiftId', data: {
        'clock_in_at': clockInAt,
        'clock_out_at': clockOutAt,
      });
    } catch (e) {
      throw toApiError(e);
    }
  }

  Future<void> setHourlyRate(String userId, int? amount) async {
    try {
      await _dio.put<dynamic>('/users/$userId/hourly-rate',
          data: {'hourly_rate_amount': amount});
    } catch (e) {
      throw toApiError(e);
    }
  }
}

final staffRepositoryProvider = Provider<StaffRepository>(
  (ref) => StaffRepository(ref.read(apiDioProvider)),
);

final staffReportProvider =
    FutureProvider.autoDispose.family<StaffReport, FinanceRange>(
  (ref, range) => ref.read(staffRepositoryProvider).report(rangeWindow(range)),
);

final shiftsProvider =
    FutureProvider.autoDispose.family<List<Shift>, FinanceRange>(
  (ref, range) => ref.read(staffRepositoryProvider).shifts(rangeWindow(range)),
);
