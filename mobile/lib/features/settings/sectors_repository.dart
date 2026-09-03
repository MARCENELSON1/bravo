import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/api_client.dart';
import '../../api/dio_errors.dart';

/// Sector/salón (backend `SectorResponse`): salón, terraza, barra…
class Sector {
  const Sector({
    required this.id,
    required this.name,
    this.color,
    this.sortOrder = 0,
  });

  final String id;
  final String name;
  final String? color;
  final int sortOrder;

  factory Sector.fromJson(Map<String, dynamic> j) => Sector(
        id: j['id'] as String,
        name: j['name'] as String,
        color: j['color'] as String?,
        sortOrder: (j['sort_order'] as int?) ?? 0,
      );
}

class SectorsRepository {
  SectorsRepository(this._dio);
  final Dio _dio;

  Future<List<Sector>> list() async {
    try {
      final res = await _dio.get<dynamic>('/sectors');
      final data = (res.data as List<dynamic>? ?? []);
      return data
          .map((r) => Sector.fromJson(Map<String, dynamic>.from(r as Map)))
          .toList();
    } catch (e) {
      throw toApiError(e);
    }
  }

  Future<void> create(String name, {String? color, int sortOrder = 0}) async {
    try {
      await _dio.post<dynamic>('/sectors',
          data: {'name': name, 'color': color, 'sort_order': sortOrder});
    } catch (e) {
      throw toApiError(e);
    }
  }

  Future<void> update(String id, String name,
      {String? color, int sortOrder = 0}) async {
    try {
      await _dio.put<dynamic>('/sectors/$id',
          data: {'name': name, 'color': color, 'sort_order': sortOrder});
    } catch (e) {
      throw toApiError(e);
    }
  }

  Future<void> delete(String id) async {
    try {
      await _dio.delete<dynamic>('/sectors/$id');
    } catch (e) {
      throw toApiError(e);
    }
  }
}

final sectorsRepositoryProvider = Provider<SectorsRepository>(
  (ref) => SectorsRepository(ref.read(apiDioProvider)),
);

final sectorsProvider = FutureProvider.autoDispose<List<Sector>>(
  (ref) => ref.read(sectorsRepositoryProvider).list(),
);
