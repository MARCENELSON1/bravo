import 'dart:convert';

import 'package:dio/dio.dart';

import '../../env/env.dart';

/// Cliente SSE en 2 pasos (espeja `frontend/src/hooks/use-realtime.ts`):
/// `POST /realtime/token` (Bearer) → token corto, luego `GET /realtime/{kind}/stream?token=`.
/// Los eventos son SEÑALES (`floor.changed`/`kds.changed`) → el consumidor refetchea.
/// Reconecta a los 3s ante error/cierre. Ignora el heartbeat (`: ping`).
class RealtimeService {
  RealtimeService(this._apiDio);

  final Dio _apiDio; // autenticado (Bearer) — para el token

  Future<String> _token() async {
    final res = await _apiDio.post<dynamic>('/realtime/token');
    return (res.data as Map)['token'] as String;
  }

  /// Emite el nombre de cada evento SSE (ej. `floor.changed`). Generador infinito:
  /// se corta cuando el consumidor cancela la suscripción.
  Stream<String> events(String kind) async* {
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
        var pending = '';
        await for (final chunk in res.data!.stream) {
          pending += utf8.decode(chunk, allowMalformed: true);
          int nl;
          while ((nl = pending.indexOf('\n')) != -1) {
            final line = pending.substring(0, nl).replaceAll('\r', '');
            pending = pending.substring(nl + 1);
            if (line.isEmpty) {
              if (eventName != null) {
                yield eventName;
                eventName = null;
              }
            } else if (line.startsWith(':')) {
              // heartbeat / comentario → ignorar
            } else if (line.startsWith('event:')) {
              eventName = line.substring(6).trim();
            }
            // `data:` no se usa: la señal alcanza para refetchear.
          }
        }
      } catch (_) {
        // conexión caída → reintentar
      }
      await Future<void>.delayed(const Duration(seconds: 3));
    }
  }
}
