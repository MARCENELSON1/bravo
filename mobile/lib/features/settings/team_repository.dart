import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/api_client.dart';
import '../../api/dio_errors.dart';

/// Invitación de un usuario al equipo (backend `POST /users/invite`). El backend
/// manda el email en español; devuelve `{message}`.
class TeamRepository {
  TeamRepository(this._dio);
  final Dio _dio;

  Future<String> invite(String email, String role) async {
    try {
      final res = await _dio.post<dynamic>('/users/invite',
          data: {'email': email, 'role': role});
      final map = Map<String, dynamic>.from(res.data as Map);
      return (map['message'] as String?) ?? '';
    } catch (e) {
      throw toApiError(e);
    }
  }
}

final teamRepositoryProvider = Provider<TeamRepository>(
  (ref) => TeamRepository(ref.read(apiDioProvider)),
);
