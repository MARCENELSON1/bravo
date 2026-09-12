// El listado de Ajustes: qué secciones se ofrecen y con qué filas.
//
// La regla de fondo es una sola —no mostrar nada que no sea cierto— y tiene dos
// caras que este test cuida por separado: una sección no puede ofrecerse si al
// entrar aparece vacía, y un ajuste no puede figurar dos veces (una editable en
// la sección y otra como texto muerto en la lista de filas).

import 'package:flutter_test/flutter_test.dart';
import 'package:wellnod_mobile/features/settings/settings_sections.dart';

SettingsTab _tab(String id) => settingsTabs.firstWhere((t) => t.id == id);

void main() {
  test('ninguna entrada del listado lleva a una sección vacía', () {
    for (final isAdmin in [true, false]) {
      for (final tab in visibleSettingsTabs(isAdmin: isAdmin)) {
        final tieneAlgo =
            tabHasSection(tab.id, isAdmin: isAdmin) ||
            visibleRows(tab).isNotEmpty;
        expect(
          tieneAlgo,
          isTrue,
          reason: '"${tab.es}" se ofrece pero no tiene nada adentro',
        );
      }
    }
  });

  test('una fila que no lee nada ni abre nada no se muestra', () {
    // "Teléfono" existe en el catálogo como mapa de lo que falta, pero no tiene
    // ni `dyn` ni `open`: mostrarla sería prometer una acción inexistente.
    final perfil = visibleRows(_tab('perfil'));
    expect(perfil.map((r) => r.es), isNot(contains('Teléfono')));
    expect(perfil.map((r) => r.es), contains('Email de contacto'));
    expect(perfil.every((r) => r.isReal), isTrue);
  });

  test('lo que la sección edita de verdad no figura además como fila muerta', () {
    // Caja, Salones, Negocio e Integraciones renderizan controles reales. Los
    // mismos ajustes están en el catálogo de filas como mapa de lo que falta,
    // pero sin `dyn` ni `open` — o sea que `isReal` los deja afuera y el dueño
    // ve un solo lugar por ajuste, el que funciona.
    const editadoPorLaSeccion = {
      'caja': ['Apertura de caja obligatoria', 'Arqueo ciego'],
      'salones': ['Sectores'],
      'negocio': ['Dirección'],
      'integraciones': ['Mercado Pago'],
    };
    for (final e in editadoPorLaSeccion.entries) {
      final filas = visibleRows(_tab(e.key)).map((r) => r.es);
      for (final nombre in e.value) {
        expect(filas, isNot(contains(nombre)), reason: '${e.key} · $nombre');
      }
    }
  });

  test('las filas visibles no dependen del rol', () {
    // Lo que cambia con el rol es qué SECCIÓN se ofrece, no qué filas tiene:
    // una fila real lo es para todos. Si esto deja de valer, el filtro de filas
    // se volvió una segunda regla de permisos escondida.
    for (final tab in settingsTabs) {
      expect(
        visibleRows(tab).length,
        tab.rows.where((r) => r.isReal).length,
        reason: tab.id,
      );
    }
  });

  test('Apariencia es de todos; las secciones de negocio son de admin', () {
    expect(tabHasSection('apariencia', isAdmin: false), isTrue);
    for (final id in [
      'caja',
      'salones',
      'negocio',
      'equipo',
      'integraciones',
    ]) {
      expect(tabHasSection(id, isAdmin: true), isTrue, reason: id);
      expect(tabHasSection(id, isAdmin: false), isFalse, reason: id);
    }
  });

  test('el listado del admin incluye las secciones funcionales', () {
    final ids = visibleSettingsTabs(isAdmin: true).map((t) => t.id);
    expect(
      ids,
      containsAll(['apariencia', 'caja', 'salones', 'equipo', 'integraciones']),
    );
    // Y deja afuera las que hoy no tienen nada real que mostrar.
    expect(ids, isNot(contains('notificaciones')));
  });
}
