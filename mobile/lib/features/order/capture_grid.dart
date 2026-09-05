import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../l10n/strings.dart';
import '../../ui/state_views.dart';
import '../../util/money.dart';
import 'capture_logic.dart';
import 'order_dtos.dart';
import 'order_providers.dart';
import 'product_dtos.dart';

/// Grilla de captura (tipo POS): búsqueda de respaldo + pestañas de categoría
/// + grilla de productos con badge de cantidad. Abre en "★ Frecuentes" (ranking
/// local por uso, `ProductUsage`) donde vive el 80% del pedido. Tap = +1 con
/// haptic; mantener = cantidad/nota. Nunca se sale de la comanda para cargar.
class CaptureGrid extends ConsumerStatefulWidget {
  const CaptureGrid({
    super.key,
    required this.order,
    required this.onAdd,
    required this.onAddWithOptions,
  });

  final Order order;
  final void Function(Product product) onAdd;
  final void Function(Product product) onAddWithOptions;

  @override
  ConsumerState<CaptureGrid> createState() => _CaptureGridState();
}

/// Pestaña "toda la carta" (las demás son categorías; null = Frecuentes).
const _allTab = '__all__';
const _favoritesLimit = 15;

class _CaptureGridState extends ConsumerState<CaptureGrid> {
  String? _tab; // null → Frecuentes
  final _search = TextEditingController();

  @override
  void initState() {
    super.initState();
    _search.addListener(() {
      if (mounted) setState(() {});
    });
  }

  @override
  void dispose() {
    _search.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final s = context.s;
    final async = ref.watch(productsProvider);
    final usage = ref.read(productUsageProvider);

    return async.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (e, _) =>
          ErrorView(error: e, onRetry: () => ref.invalidate(productsProvider)),
      data: (all) {
        final orderable = all.where((p) => p.orderable).toList();
        final categories = categoriesOf(orderable);
        final query = _search.text;
        final searching = query.trim().isNotEmpty;
        final List<Product> shown;
        if (searching) {
          shown = filterProducts(orderable, query: query);
        } else if (_tab == null) {
          shown = usage.rank(orderable).take(_favoritesLimit).toList();
        } else if (_tab == _allTab) {
          shown = orderable;
        } else {
          shown = filterProducts(orderable, category: _tab);
        }
        return Column(
          children: [
            _searchField(s),
            _tabs(s, categories, dimmed: searching),
            Expanded(
              child: shown.isEmpty
                  ? Center(child: Text(s.captureNoResults))
                  : _grid(shown),
            ),
          ],
        );
      },
    );
  }

  Widget _searchField(Strings s) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 6, 16, 6),
      child: TextField(
        controller: _search,
        decoration: InputDecoration(
          hintText: s.searchProduct,
          prefixIcon: const Icon(Icons.search),
          isDense: true,
          suffixIcon: _search.text.isEmpty
              ? null
              : IconButton(
                  icon: const Icon(Icons.close),
                  onPressed: () => _search.clear(),
                ),
        ),
      ),
    );
  }

  Widget _tabs(Strings s, List<String> categories, {required bool dimmed}) {
    final entries = <MapEntry<String?, String>>[
      MapEntry(null, s.chipFavorites),
      MapEntry(_allTab, s.chipAllProducts),
      for (final c in categories) MapEntry(c, c),
    ];
    return Opacity(
      opacity: dimmed ? 0.45 : 1,
      child: SizedBox(
        height: 44,
        child: ListView(
          scrollDirection: Axis.horizontal,
          padding: const EdgeInsets.symmetric(horizontal: 16),
          children: [
            for (final e in entries)
              Padding(
                padding: const EdgeInsets.only(right: 8),
                child: ChoiceChip(
                  label: Text(e.value),
                  selected: !dimmed && _tab == e.key,
                  onSelected: (_) {
                    HapticFeedback.selectionClick();
                    setState(() {
                      _tab = e.key;
                      _search.clear();
                    });
                  },
                ),
              ),
          ],
        ),
      ),
    );
  }

  Widget _grid(List<Product> products) {
    return GridView.builder(
      padding: const EdgeInsets.fromLTRB(16, 4, 16, 12),
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 3,
        mainAxisSpacing: 10,
        crossAxisSpacing: 10,
        childAspectRatio: 1.12,
      ),
      itemCount: products.length,
      itemBuilder: (context, i) {
        final p = products[i];
        return _ProductTile(
          product: p,
          count: pendingQtyOf(widget.order, p.id),
          onTap: () {
            HapticFeedback.selectionClick();
            widget.onAdd(p);
          },
          onLongPress: () {
            HapticFeedback.mediumImpact();
            widget.onAddWithOptions(p);
          },
        );
      },
    );
  }
}

class _ProductTile extends StatelessWidget {
  const _ProductTile({
    required this.product,
    required this.count,
    required this.onTap,
    required this.onLongPress,
  });

  final Product product;
  final int count;
  final VoidCallback onTap;
  final VoidCallback onLongPress;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final scheme = theme.colorScheme;
    final has = count > 0;
    return Stack(
      clipBehavior: Clip.none,
      children: [
        Material(
          color: has
              ? scheme.primary.withValues(alpha: 0.14)
              : scheme.surface.withValues(alpha: 0.55),
          borderRadius: BorderRadius.circular(14),
          child: InkWell(
            onTap: onTap,
            onLongPress: onLongPress,
            borderRadius: BorderRadius.circular(14),
            child: Container(
              padding: const EdgeInsets.fromLTRB(10, 10, 10, 8),
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(14),
                border: Border.all(
                  color: has
                      ? scheme.primary.withValues(alpha: 0.6)
                      : scheme.outlineVariant.withValues(alpha: 0.5),
                ),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Expanded(
                    child: Text(
                      product.name,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: theme.textTheme.bodyMedium?.copyWith(
                        fontWeight: FontWeight.w600,
                        height: 1.15,
                      ),
                    ),
                  ),
                  Row(
                    children: [
                      Expanded(
                        child: Text(
                          formatMoney(product.priceAmount, product.currency),
                          style: theme.textTheme.labelSmall?.copyWith(
                            color: scheme.onSurfaceVariant,
                          ),
                        ),
                      ),
                      // Tiene grupo obligatorio: al tocar, primero se elige.
                      if (product.needsChoice)
                        Icon(Icons.tune, size: 13, color: scheme.primary),
                    ],
                  ),
                ],
              ),
            ),
          ),
        ),
        if (has)
          Positioned(
            top: -7,
            right: -6,
            child: Container(
              constraints: const BoxConstraints(minWidth: 22),
              height: 22,
              padding: const EdgeInsets.symmetric(horizontal: 6),
              alignment: Alignment.center,
              decoration: BoxDecoration(
                color: scheme.primary,
                borderRadius: BorderRadius.circular(999),
              ),
              child: Text(
                '$count',
                style: TextStyle(
                  color: scheme.onPrimary,
                  fontSize: 12,
                  fontWeight: FontWeight.w800,
                ),
              ),
            ),
          ),
      ],
    );
  }
}
