// El detalle de un plato en Finanzas: lo que decide qué se muestra.
//
// El riesgo de esta pantalla no es el dibujo, es leer mal el contrato: los
// totales cubren el período entero y el listado viene ACOTADO. Confundirlos
// haría que un plato muy vendido mostrara de menos sin decirlo.

import 'package:flutter_test/flutter_test.dart';
import 'package:wellnod_mobile/features/finance/finance_repository.dart';

void main() {
  group('ProductDetail', () {
    test('los totales NO se derivan del listado acotado', () {
      // El backend manda 3 unidades vendidas pero una sola línea: el listado
      // está cortado. Sumar las líneas daría 1 y sería mentira.
      final d = ProductDetail.fromJson({
        'currency': 'ARS',
        'units_sold': 3,
        'sales_amount': 150000,
        'food_cost_amount': 60000,
        'margin_amount': 90000,
        'lines': [
          {
            'occurred_at': '2026-09-10T14:00:00+00:00',
            'quantity': 1,
            'line_amount': 50000,
            'margin_amount': 30000,
          }
        ],
        'cost_series': [],
        'lines_truncated': true,
      });

      expect(d.unitsSold, 3, reason: 'el total es del período, no del listado');
      expect(d.lines.length, 1);
      expect(d.linesTruncated, isTrue, reason: 'la UI tiene que poder avisarlo');
    });

    test('un backend sin los campos nuevos no rompe la pantalla', () {
      final d = ProductDetail.fromJson({
        'currency': 'ARS',
        'units_sold': 1,
        'sales_amount': 1000,
        'food_cost_amount': 0,
        'margin_amount': 1000,
        'lines': [],
      });

      expect(d.costSeries, isEmpty);
      expect(d.linesTruncated, isFalse);
    });

    test('la serie de costo llega ordenada y con su valor', () {
      final d = ProductDetail.fromJson({
        'currency': 'ARS',
        'units_sold': 2,
        'sales_amount': 2000,
        'food_cost_amount': 800,
        'margin_amount': 1200,
        'lines': [],
        'cost_series': [
          {'day': '2026-09-01', 'unit_cost': 300},
          {'day': '2026-09-02', 'unit_cost': 500},
        ],
        'lines_truncated': false,
      });

      expect(d.costSeries.map((p) => p.unitCost).toList(), [300, 500]);
      expect(d.costSeries.first.day, '2026-09-01');
    });
  });
}
