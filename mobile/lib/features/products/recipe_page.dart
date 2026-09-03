import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/api_error.dart';
import '../../l10n/strings.dart';
import '../../ui/app_background.dart';
import '../../ui/glass_panel.dart';
import '../inventory/inventory_repository.dart';
import 'recipe_repository.dart';

/// Editor de receta de un producto (Fase 6): edita las líneas de insumo y
/// preserva las de preparación. El food cost lo recalcula el backend.
class RecipePage extends ConsumerStatefulWidget {
  const RecipePage({super.key, required this.productId, required this.productName});

  final String productId;
  final String productName;

  @override
  ConsumerState<RecipePage> createState() => _RecipePageState();
}

class _RecipePageState extends ConsumerState<RecipePage> {
  List<RecipeItem>? _lines;

  @override
  Widget build(BuildContext context) {
    final s = context.s;
    final recipe = ref.watch(recipeProvider(widget.productId));
    final ingredients = ref.watch(ingredientsProvider);

    return Scaffold(
      backgroundColor: Colors.transparent,
      appBar: AppBar(
        title: Text('${s.recetaTitle} · ${widget.productName}'),
        backgroundColor: Colors.transparent,
      ),
      body: Stack(
        children: [
          const AppBackground(),
          SafeArea(child: _body(s, recipe, ingredients)),
        ],
      ),
    );
  }

  Widget _body(
    Strings s,
    AsyncValue<Recipe> recipe,
    AsyncValue<List<Ingredient>> ingredients,
  ) {
    if (recipe.isLoading || ingredients.isLoading) {
      return const Center(child: CircularProgressIndicator());
    }
    final err = recipe.error ?? ingredients.error;
    if (err != null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Text(err is ApiError ? err.message : '$err'),
        ),
      );
    }
    _lines ??= [...recipe.value!.items];
    return _editor(s, ingredients.value!);
  }

  Widget _editor(Strings s, List<Ingredient> ings) {
    final byId = {for (final i in ings) i.id: i};
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        GlassPanel(
          padding: const EdgeInsets.symmetric(vertical: 4),
          child: Material(
            type: MaterialType.transparency,
            child: _lines!.isEmpty
                ? Padding(padding: const EdgeInsets.all(16), child: Text(s.recetaEmpty))
                : Column(
                    children: [
                      for (var i = 0; i < _lines!.length; i++) ...[
                        if (i > 0) const Divider(height: 1),
                        _lineTile(s, byId, i),
                      ],
                    ],
                  ),
          ),
        ),
        const SizedBox(height: 12),
        OutlinedButton.icon(
          onPressed: () => _addLine(s, ings),
          icon: const Icon(Icons.add),
          label: Text(s.recetaAdd),
        ),
        const SizedBox(height: 12),
        FilledButton.icon(
          onPressed: () => _save(s),
          icon: const Icon(Icons.save_outlined),
          label: Text(s.setSave),
        ),
      ],
    );
  }

  Widget _lineTile(Strings s, Map<String, Ingredient> byId, int idx) {
    final line = _lines![idx];
    if (line.isPreparation) {
      return ListTile(
        leading: const Icon(Icons.blender_outlined),
        title: Text(s.recetaPrep),
        subtitle: Text('${s.qtyLabel}: ${line.qty}'),
      );
    }
    final ing = byId[line.ingredientId];
    return ListTile(
      title: Text(ing?.name ?? line.ingredientId ?? '?'),
      subtitle: Text('${line.qty} ${ing?.unit ?? ''}'),
      trailing: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          IconButton(
            icon: const Icon(Icons.edit_outlined, size: 18),
            onPressed: () => _editQty(s, idx),
          ),
          IconButton(
            icon: const Icon(Icons.delete_outline, size: 18),
            onPressed: () => setState(() => _lines!.removeAt(idx)),
          ),
        ],
      ),
    );
  }

  Future<void> _editQty(Strings s, int idx) async {
    final line = _lines![idx];
    final qty = await _askQty(s, initial: line.qty);
    if (qty == null) return;
    setState(() => _lines![idx] = RecipeItem(
          qty: qty,
          ingredientId: line.ingredientId,
          preparationId: line.preparationId,
        ));
  }

  Future<void> _addLine(Strings s, List<Ingredient> ings) async {
    final picked = await showModalBottomSheet<Ingredient>(
      context: context,
      isScrollControlled: true,
      builder: (ctx) => SizedBox(
        height: MediaQuery.of(ctx).size.height * 0.7,
        child: ListView(
          children: [
            for (final i in ings)
              ListTile(
                title: Text(i.name),
                subtitle: Text(i.unit),
                onTap: () => Navigator.of(ctx).pop(i),
              ),
          ],
        ),
      ),
    );
    if (picked == null) return;
    final qty = await _askQty(s, initial: 0);
    if (qty == null || qty <= 0) return;
    setState(() => _lines!.add(RecipeItem(qty: qty, ingredientId: picked.id)));
  }

  Future<int?> _askQty(Strings s, {required int initial}) async {
    final ctrl = TextEditingController(text: initial > 0 ? '$initial' : '');
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(s.qtyLabel),
        content: TextField(
          controller: ctrl,
          autofocus: true,
          keyboardType: TextInputType.number,
          decoration: InputDecoration(labelText: s.qtyLabel),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(false),
            child: Text(MaterialLocalizations.of(ctx).cancelButtonLabel),
          ),
          FilledButton(
            onPressed: () => Navigator.of(ctx).pop(true),
            child: Text(MaterialLocalizations.of(ctx).okButtonLabel),
          ),
        ],
      ),
    );
    if (ok != true) return null;
    return int.tryParse(ctrl.text.trim());
  }

  Future<void> _save(Strings s) async {
    try {
      await ref.read(recipeRepositoryProvider).set(widget.productId, _lines!);
      ref.invalidate(recipeProvider(widget.productId));
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(s.recetaSaved)));
      }
    } on ApiError catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(e.message)));
      }
    }
  }
}
