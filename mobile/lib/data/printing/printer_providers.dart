import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../theme/theme_controller.dart';
import 'printer_service.dart';

final printerServiceProvider = Provider<PrinterService>(
  (ref) => PrinterService(ref.read(sharedPreferencesProvider)),
);
