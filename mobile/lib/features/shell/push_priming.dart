import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../../l10n/strings.dart';

/// Explicar antes de pedir el permiso de notificaciones.
///
/// iOS pregunta **una sola vez**: si el mozo toca "No permitir" en el diálogo del
/// sistema, no hay forma de volver a pedirlo desde la app y pierde el aviso de
/// "mesa lista" para siempre — que es la razón por la que la app le sirve en el
/// bolsillo. Antes se pedía en frío, apenas entraba, sin decir para qué.
///
/// Esta hoja va primero y no es un permiso: es la explicación. Si dice que no,
/// no se dispara el diálogo del sistema y **queda la puerta abierta** para
/// preguntarle en otro momento. Se recuerda la respuesta para no insistir en
/// cada arranque.
class PushPriming {
  static const _key = 'push_priming_answered_v1';

  /// ¿Ya decidimos pedirle el permiso al sistema? `false` = todavía no, o dijo
  /// "ahora no" y hay que respetarlo.
  static Future<bool> shouldAsk(BuildContext context) async {
    final prefs = await SharedPreferences.getInstance();
    if (prefs.getBool(_key) == true) return true; // ya aceptó explicar → seguir
    if (prefs.containsKey(_key)) return false; // dijo "ahora no"
    if (!context.mounted) return false;

    final accepted = await showModalBottomSheet<bool>(
          context: context,
          isScrollControlled: true,
          showDragHandle: true,
          builder: (_) => const _PrimingSheet(),
        ) ??
        false;
    await prefs.setBool(_key, accepted);
    return accepted;
  }
}

class _PrimingSheet extends StatelessWidget {
  const _PrimingSheet();

  @override
  Widget build(BuildContext context) {
    final s = context.s;
    final theme = Theme.of(context);
    final scheme = theme.colorScheme;
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(24, 8, 24, 24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(Icons.notifications_active_outlined,
                size: 36, color: scheme.primary),
            const SizedBox(height: 14),
            Semantics(
              header: true,
              child: Text(s.pushPrimingTitle,
                  style: theme.textTheme.titleLarge
                      ?.copyWith(fontWeight: FontWeight.w700)),
            ),
            const SizedBox(height: 10),
            Text(s.pushPrimingBody,
                style: TextStyle(color: scheme.onSurfaceVariant, height: 1.4)),
            const SizedBox(height: 24),
            FilledButton(
              onPressed: () => Navigator.of(context).pop(true),
              style: FilledButton.styleFrom(minimumSize: const Size.fromHeight(52)),
              child: Text(s.pushPrimingAccept),
            ),
            const SizedBox(height: 8),
            TextButton(
              onPressed: () => Navigator.of(context).pop(false),
              style: TextButton.styleFrom(minimumSize: const Size.fromHeight(48)),
              child: Text(s.pushPrimingLater),
            ),
          ],
        ),
      ),
    );
  }
}
