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
import 'product_tile_style.dart';

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
        childAspectRatio: 1.0,
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
    final accent = categoryAccent(product.category, product.station);
    final icon = categoryIcon(product.category, product.station);
    final url = product.imageUrl;
    final hasImage = url != null && url.isNotEmpty;

    return Stack(
      clipBehavior: Clip.none,
      children: [
        Material(
          color: Colors.transparent,
          borderRadius: BorderRadius.circular(16),
          clipBehavior: Clip.antiAlias,
          child: InkWell(
            onTap: onTap,
            onLongPress: onLongPress,
            child: Ink(
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(16),
                // Tinte de la categoría; si ya está en la comanda, el primario manda.
                color: has
                    ? scheme.primary.withValues(alpha: 0.16)
                    : accent.withValues(alpha: 0.10),
                border: Border.all(
                  color: has
                      ? scheme.primary.withValues(alpha: 0.65)
                      : accent.withValues(alpha: 0.28),
                ),
              ),
              child: hasImage
                  ? _WithImage(
                      product: product,
                      url: url,
                      accent: accent,
                      icon: icon,
                      fallback: _Plain(
                        product: product,
                        accent: accent,
                        icon: icon,
                      ),
                    )
                  : _Plain(product: product, accent: accent, icon: icon),
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

/// Tile sin foto: categoría (ícono + nombre) arriba, nombre del plato grande,
/// precio abajo, y el ícono como marca de agua para darle textura.
class _Plain extends StatelessWidget {
  const _Plain({
    required this.product,
    required this.accent,
    required this.icon,
  });

  final Product product;
  final Color accent;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final scheme = theme.colorScheme;
    return Stack(
      clipBehavior: Clip.hardEdge,
      children: [
        Positioned(
          right: -8,
          bottom: -10,
          child: Icon(icon, size: 58, color: accent.withValues(alpha: 0.13)),
        ),
        Padding(
          padding: const EdgeInsets.fromLTRB(10, 9, 10, 8),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Icon(icon, size: 13, color: accent),
                  const SizedBox(width: 4),
                  Expanded(
                    child: Text(
                      product.category ?? '',
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: theme.textTheme.labelSmall?.copyWith(
                        color: accent,
                        fontWeight: FontWeight.w600,
                        letterSpacing: 0.2,
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 5),
              Expanded(
                child: Text(
                  product.name,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: theme.textTheme.titleSmall?.copyWith(
                    fontWeight: FontWeight.w700,
                    height: 1.15,
                  ),
                ),
              ),
              Row(
                children: [
                  Expanded(
                    child: Text(
                      formatMoney(product.priceAmount, product.currency),
                      style: theme.textTheme.labelMedium?.copyWith(
                        fontWeight: FontWeight.w600,
                        color: scheme.onSurface.withValues(alpha: 0.85),
                      ),
                    ),
                  ),
                  // Tiene grupo obligatorio: al tocar, primero se elige.
                  if (product.needsChoice)
                    Icon(Icons.tune, size: 14, color: scheme.primary),
                ],
              ),
            ],
          ),
        ),
      ],
    );
  }
}

/// Tile con foto: la imagen llena la tile con un degradé abajo y el nombre
/// encima; franja de la categoría arriba. Si la foto falla, cae a la simple.
class _WithImage extends StatelessWidget {
  const _WithImage({
    required this.product,
    required this.url,
    required this.accent,
    required this.icon,
    required this.fallback,
  });

  final Product product;
  final String url;
  final Color accent;
  final IconData icon;
  final Widget fallback;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Stack(
      fit: StackFit.expand,
      children: [
        Image.network(
          url,
          fit: BoxFit.cover,
          errorBuilder: (_, _, _) => fallback,
          loadingBuilder: (_, child, progress) =>
              progress == null ? child : fallback,
        ),
        const DecoratedBox(
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topCenter,
              end: Alignment.bottomCenter,
              stops: [0.3, 1],
              colors: [Colors.transparent, Color(0xCC000000)],
            ),
          ),
        ),
        Positioned(
          top: 0,
          left: 0,
          right: 0,
          child: Container(height: 3, color: accent),
        ),
        Padding(
          padding: const EdgeInsets.fromLTRB(10, 9, 10, 8),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.end,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                product.name,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: theme.textTheme.titleSmall?.copyWith(
                  color: Colors.white,
                  fontWeight: FontWeight.w700,
                  height: 1.15,
                ),
              ),
              const SizedBox(height: 2),
              Row(
                children: [
                  Expanded(
                    child: Text(
                      formatMoney(product.priceAmount, product.currency),
                      style: theme.textTheme.labelMedium?.copyWith(
                        color: Colors.white.withValues(alpha: 0.85),
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                  if (product.needsChoice)
                    const Icon(Icons.tune, size: 14, color: Colors.white),
                ],
              ),
            ],
          ),
        ),
      ],
    );
  }
}
