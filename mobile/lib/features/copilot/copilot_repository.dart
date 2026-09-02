import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/api_client.dart';
import '../../api/dio_errors.dart';

/// Respuesta del copiloto (backend `CopilotAnswerResponse`): texto en lenguaje
/// natural + la tabla (columnas/filas) que respalda la respuesta.
class CopilotAnswer {
  const CopilotAnswer({
    required this.answer,
    required this.columns,
    required this.rows,
    required this.llmEnabled,
  });

  final String answer;
  final List<String> columns;
  final List<List<dynamic>> rows;
  final bool llmEnabled;

  factory CopilotAnswer.fromJson(Map<String, dynamic> j) => CopilotAnswer(
        answer: (j['answer'] as String?) ?? '',
        columns: ((j['columns'] as List?) ?? const []).map((e) => '$e').toList(),
        rows: ((j['rows'] as List?) ?? const [])
            .map((r) => (r as List).toList())
            .toList(),
        llmEnabled: (j['llm_enabled'] as bool?) ?? false,
      );
}

class CopilotRepository {
  CopilotRepository(this._dio);

  final Dio _dio;

  Future<CopilotAnswer> ask(String question) async {
    try {
      final res = await _dio.post<dynamic>(
        '/copilot/ask',
        data: {'question': question},
      );
      return CopilotAnswer.fromJson(Map<String, dynamic>.from(res.data as Map));
    } catch (e) {
      throw toApiError(e);
    }
  }
}

final copilotRepositoryProvider = Provider<CopilotRepository>(
  (ref) => CopilotRepository(ref.read(apiDioProvider)),
);
