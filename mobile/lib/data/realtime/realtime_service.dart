import 'dart:convert';

import 'package:dio/dio.dart';

import '../../env/env.dart';

/// Un evento SSE: nombre (`floor.changed`, `order.ready`, …) + payload. El
/// backend manda `event: <tipo>\ndata: <json>\n\n`; para las señales de refetch
/// el `data` viene vacío, y para las dirigidas (ej. `order.ready`) trae ids.
class RealtimeEvent {
  const RealtimeEvent(this.name, this.data);
  final String name;
  final Map<String, dynamic> data;
}

/// Cliente SSE en 2 pasos (espeja `frontend/src/hooks/use-realtime.ts`):
/// `POST /realtime/token` (Bearer) → token corto, luego `GET /realtime/{kind}/stream?token=`.
/// Reconecta a los 3s ante error/cierre. Ignora el heartbeat (`: ping`).
class RealtimeService {
  RealtimeService(this._apiDio);

  final Dio _apiDio; // autenticado (Bearer) — para el token

  Future<String> _token() async {
    final res = await _apiDio.post<dynamic>('/realtime/token');
    return (res.data as Map)['token'] as String;
  }

  /// Emite cada evento SSE (nombre + payload). Generador infinito: se corta
  /// cuando el consumidor cancela la suscripción.
  Stream<RealtimeEvent> events(String kind) async* {
    while (true) {
      try {
        final token = await _token();
        final streamDio = Dio(BaseOptions(baseUrl: Env.apiBaseUrl));
        final res = await streamDio.get<ResponseBody>(
          '/realtime/$kind/stream',
          queryParameters: {'token': token},
          options: Options(
            responseType: ResponseType.stream,
            headers: {'Accept': 'text/event-stream'},
          ),
        );

        String? eventName;
        var dataBuf = '';
        var pending = '';
        await for (final chunk in res.data!.stream) {
          pending += utf8.decode(chunk, allowMalformed: true);
          int nl;
          while ((nl = pending.indexOf('\n')) != -1) {
            final line = pending.substring(0, nl).replaceAll('\r', '');
            pending = pending.substring(nl + 1);
            if (line.isEmpty) {
              if (eventName != null) {
                yield RealtimeEvent(eventName, _parseData(dataBuf));
                eventName = null;
                dataBuf = '';
              }
            } else if (line.startsWith(':')) {
              // heartbeat / comentario → ignorar
            } else if (line.startsWith('event:')) {
              eventName = line.substring(6).trim();
            } else if (line.startsWith('data:')) {
              dataBuf += line.substring(5).trim();
            }
          }
        }
      } catch (_) {
        // conexión caída → reintentar
      }
      await Future<void>.delayed(const Duration(seconds: 3));
    }
  }

  Map<String, dynamic> _parseData(String buf) {
    if (buf.isEmpty) return const {};
    try {
      final decoded = jsonDecode(buf);
      return decoded is Map ? Map<String, dynamic>.from(decoded) : const {};
    } catch (_) {
      return const {};
    }
  }
}
