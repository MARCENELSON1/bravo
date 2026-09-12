import 'floor_dtos.dart';
import 'floor_view.dart';

/// Lentes del piso (espeja `frontend/src/lib/floor-filter.ts`).
enum FloorFilter { all, toServe, toCharge, mine, free }

List<FloorTable> filterFloor(
  List<FloorTable> tables,
  FloorFilter filter,
  String? currentUserId,
) {
  return tables.where((t) {
    final view = floorView(t);
    switch (filter) {
      case FloorFilter.all:
        return true;
      case FloorFilter.toServe:
        return view.status == FloorStatus.toServe;
      case FloorFilter.toCharge:
        return view.status == FloorStatus.served ||
            view.status == FloorStatus.toCharge;
      case FloorFilter.mine:
        return t.session?.waiterId != null &&
            t.session!.waiterId == currentUserId;
      case FloorFilter.free:
        return t.isFree;
    }
  }).toList();
}
