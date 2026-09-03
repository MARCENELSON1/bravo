// Estructura de la pantalla de Ajustes, portada 1:1 de `config-page.tsx` del web:
// 13 tabs con filas. Las tabs con contenido funcional (apariencia, caja, salones,
// negocio, equipo, integraciones, ia) renderizan widgets reales en `ajustes_page`;
// el resto de las filas son "Próximamente" (igual que en la web).

class SettingRow {
  const SettingRow(
    this.es,
    this.en, {
    this.descEs,
    this.descEn,
    this.valueEs,
    this.valueEn,
    this.action,
    this.toggle = false,
    this.dyn,
    this.danger = false,
  });

  final String es;
  final String en;
  final String? descEs;
  final String? descEn;
  final String? valueEs;
  final String? valueEn;
  final String? action; // change|edit|configure|upload|choose|view|manage|connect|export|delete
  final bool toggle;
  final String? dyn; // name|email|tenant|avatar → valor real de la sesión
  final bool danger;

  String label(bool en) => en ? this.en : es;
  String? desc(bool en) => en ? descEn : descEs;
  String? value(bool en) => en ? valueEn : valueEs;
}

class SettingsTab {
  const SettingsTab(this.id, this.es, this.en, this.rows);
  final String id;
  final String es;
  final String en;
  final List<SettingRow> rows;
  String title(bool en) => en ? this.en : es;
}

String settingsActionLabel(String action, bool en) => switch (action) {
      'change' => en ? 'Change' : 'Cambiar',
      'edit' => en ? 'Edit' : 'Editar',
      'configure' => en ? 'Configure' : 'Configurar',
      'upload' => en ? 'Upload' : 'Cargar',
      'choose' => en ? 'Choose' : 'Elegir',
      'view' => en ? 'View' : 'Ver',
      'manage' => en ? 'Manage' : 'Gestionar',
      'connect' => en ? 'Connect' : 'Conectar',
      'export' => en ? 'Export' : 'Exportar',
      'delete' => en ? 'Delete' : 'Eliminar',
      _ => action,
    };

const settingsTabs = <SettingsTab>[
  SettingsTab('perfil', 'Mi perfil', 'My profile', [
    SettingRow('Foto de perfil', 'Profile photo',
        descEs: 'Se muestra en tu perfil.', descEn: 'Shown on your profile.',
        action: 'change', dyn: 'avatar'),
    SettingRow('Nombre completo', 'Full name', dyn: 'name'),
    SettingRow('Email de contacto', 'Contact email', dyn: 'email'),
    SettingRow('Teléfono', 'Phone', action: 'edit'),
    SettingRow('Idioma', 'Language',
        valueEs: 'Español (Argentina)', valueEn: 'Spanish (Argentina)'),
    SettingRow('Zona horaria', 'Time zone',
        valueEs: 'GMT−3 · Buenos Aires', valueEn: 'GMT−3 · Buenos Aires'),
    SettingRow('Formato de hora', 'Time format', valueEs: '24 h', valueEn: '24 h'),
    SettingRow('Pantalla de inicio', 'Home screen',
        descEs: 'Adónde entrás al abrir la app.',
        descEn: 'Where you land when you open the app.',
        valueEs: 'Inicio', valueEn: 'Home'),
  ]),
  SettingsTab('apariencia', 'Apariencia', 'Appearance', [
    SettingRow('Densidad', 'Density',
        descEs: 'Espaciado de la interfaz.', descEn: 'Interface spacing.',
        valueEs: 'Cómoda', valueEn: 'Comfortable'),
    SettingRow('Tamaño de texto', 'Text size', valueEs: 'Normal', valueEn: 'Normal'),
    SettingRow('Color de acento', 'Accent color', action: 'choose'),
    SettingRow('Alto contraste', 'High contrast', toggle: true),
    SettingRow('Sidebar colapsado', 'Collapsed sidebar', toggle: true),
    SettingRow('Vista de mesas por defecto', 'Default table view',
        valueEs: 'Plano', valueEn: 'Floor'),
    SettingRow('Decimales en precios', 'Price decimals', valueEs: '2', valueEn: '2'),
  ]),
  SettingsTab('seguridad', 'Seguridad', 'Security', [
    SettingRow('Contraseña', 'Password',
        descEs: 'Actualizá tu contraseña.', descEn: 'Update your password.',
        action: 'change'),
    SettingRow('Verificación en dos pasos (2FA)', 'Two-factor (2FA)', toggle: true),
    SettingRow('PIN de acceso rápido', 'Quick access PIN',
        descEs: 'Para operar sin re-ingresar.',
        descEn: 'Operate without re-logging in.', action: 'configure'),
    SettingRow('Bloqueo por inactividad', 'Inactivity lock',
        valueEs: 'Desactivado', valueEn: 'Off'),
    SettingRow('Pedir contraseña para anular o descontar',
        'Require password to void or discount', toggle: true),
    SettingRow('Sesiones activas', 'Active sessions', action: 'view'),
    SettingRow('Historial de accesos', 'Access history', action: 'view'),
  ]),
  SettingsTab('notificaciones', 'Notificaciones', 'Notifications', [
    SettingRow('Canales', 'Channels',
        descEs: 'Email, push, WhatsApp.', descEn: 'Email, push, WhatsApp.',
        action: 'configure'),
    SettingRow('Eventos que avisan', 'Alerting events', action: 'configure'),
    SettingRow('Umbral de mesa demorada', 'Delayed table threshold',
        valueEs: '20 min', valueEn: '20 min'),
    SettingRow('Resumen diario', 'Daily summary',
        descEs: 'Y a qué hora te llega.', descEn: 'And what time it arrives.',
        action: 'configure'),
    SettingRow('No molestar', 'Do not disturb', toggle: true),
    SettingRow('Sonido de alertas', 'Alert sound', toggle: true),
  ]),
  SettingsTab('facturacion', 'Facturación electrónica', 'E-invoicing', [
    SettingRow('CUIT', 'CUIT', action: 'edit'),
    SettingRow('Condición frente al IVA', 'VAT condition', action: 'edit'),
    SettingRow('Certificado ARCA', 'ARCA certificate',
        descEs: 'Certificado y clave fiscal.', descEn: 'Certificate and fiscal key.',
        action: 'upload'),
    SettingRow('Ambiente', 'Environment',
        descEs: 'Homologación o producción.', descEn: 'Sandbox or production.',
        valueEs: 'Homologación', valueEn: 'Sandbox'),
    SettingRow('Puntos de venta', 'Sales points', action: 'configure'),
    SettingRow('Emisión automática al cerrar mesa', 'Auto-issue on table close',
        toggle: true),
    SettingRow('Comprobante por defecto', 'Default receipt',
        valueEs: 'Ticket B', valueEn: 'Ticket B'),
    SettingRow('Envío al cliente', 'Send to customer',
        descEs: 'Comprobante por email o WhatsApp.',
        descEn: 'Receipt by email or WhatsApp.', action: 'configure'),
  ]),
  SettingsTab('negocio', 'Datos del local', 'Business', [
    SettingRow('Nombre', 'Name', action: 'edit', dyn: 'tenant'),
    SettingRow('Logo', 'Logo', action: 'upload'),
    SettingRow('Dirección', 'Address', action: 'edit'),
    SettingRow('Teléfono', 'Phone', action: 'edit'),
    SettingRow('Horarios de atención', 'Business hours', action: 'configure'),
    SettingRow('Capacidad', 'Capacity',
        descEs: 'Cantidad de cubiertos.', descEn: 'Number of seats.', action: 'edit'),
    SettingRow('Precios con IVA incluido', 'Prices include VAT', toggle: true),
    SettingRow('Redondeo', 'Rounding', valueEs: 'Sin redondeo', valueEn: 'None'),
    SettingRow('Cubierto', 'Cover charge',
        descEs: 'Cargo por cubierto.', descEn: 'Per-seat charge.', action: 'configure'),
    SettingRow('Propina sugerida', 'Suggested tip', valueEs: '10%', valueEn: '10%'),
  ]),
  SettingsTab('salones', 'Salones y mesas', 'Floor & tables', [
    SettingRow('Sectores', 'Sectors',
        descEs: 'Salón, terraza, barra…', descEn: 'Dining room, terrace, bar…',
        action: 'configure'),
    SettingRow('Mesas y cubiertos', 'Tables & seats', action: 'configure'),
    SettingRow('Numeración automática', 'Auto numbering', toggle: true),
    SettingRow('Unir y dividir mesas', 'Merge & split tables', toggle: true),
  ]),
  SettingsTab('caja', 'Caja y pagos', 'Cash & payments', [
    SettingRow('Medios de pago', 'Payment methods', action: 'configure'),
    SettingRow('Apertura de caja obligatoria', 'Require open cash', toggle: true),
    SettingRow('Arqueo ciego', 'Blind count',
        descEs: 'Sin ver el esperado al cerrar.',
        descEn: 'Close without seeing the expected total.', toggle: true),
    SettingRow('Diferencia tolerada', 'Tolerated difference',
        valueEs: r'$0', valueEn: r'$0'),
    SettingRow('Reparto de propinas', 'Tip sharing', action: 'configure'),
    SettingRow('Límite de descuento por rol', 'Discount limit by role',
        action: 'configure'),
    SettingRow('Cuenta corriente', 'House account', action: 'configure'),
  ]),
  SettingsTab('comandas', 'Comandas e impresión', 'Orders & printing', [
    SettingRow('Impresoras por sector', 'Printers by sector', action: 'configure'),
    SettingRow('Ruteo de categoría a impresora', 'Category-to-printer routing',
        action: 'configure'),
    SettingRow('Copias', 'Copies', valueEs: '1', valueEn: '1'),
    SettingRow('Formato de ticket', 'Ticket format', action: 'configure'),
    SettingRow('Tiempo de alerta del KDS', 'KDS alert time',
        valueEs: '8 min', valueEn: '8 min'),
    SettingRow('Impresión automática', 'Auto print', toggle: true),
  ]),
  SettingsTab('equipo', 'Equipo', 'Team', [
    SettingRow('Usuarios', 'Users', action: 'manage'),
    SettingRow('Roles y permisos', 'Roles & permissions', action: 'configure'),
    SettingRow('PIN por empleado', 'PIN per employee', action: 'configure'),
    SettingRow('Turnos', 'Shifts', action: 'configure'),
    SettingRow('Tolerancia de fichaje', 'Clock-in tolerance',
        valueEs: '10 min', valueEn: '10 min'),
    SettingRow('Geocerca', 'Geofence',
        descEs: 'Fichaje dentro del local.', descEn: 'Clock in inside the venue.',
        action: 'configure'),
  ]),
  SettingsTab('ia', 'IA Insights', 'AI Insights', [
    SettingRow('Acceso a datos por módulo', 'Data access by module',
        action: 'configure'),
    SettingRow('Nivel de autonomía', 'Autonomy level',
        valueEs: 'Sugerencias', valueEn: 'Suggestions'),
    SettingRow('Umbrales de alerta', 'Alert thresholds', action: 'edit'),
    SettingRow('Frecuencia del resumen', 'Summary frequency',
        valueEs: 'Diario', valueEn: 'Daily'),
    SettingRow('Privacidad', 'Privacy', action: 'configure'),
  ]),
  SettingsTab('integraciones', 'Integraciones', 'Integrations', [
    SettingRow('Mercado Pago', 'Mercado Pago', action: 'connect'),
    SettingRow('PedidosYa', 'PedidosYa', action: 'connect'),
    SettingRow('Rappi', 'Rappi', action: 'connect'),
    SettingRow('WhatsApp', 'WhatsApp', action: 'connect'),
    SettingRow('API y webhooks', 'API & webhooks', action: 'configure'),
  ]),
  SettingsTab('cuenta', 'Cuenta', 'Account', [
    SettingRow('Plan y uso', 'Plan & usage',
        descEs: 'Tu plan de Wellnod.', descEn: 'Your Wellnod plan.', action: 'view'),
    SettingRow('Facturas de Wellnod', 'Wellnod invoices', action: 'view'),
    SettingRow('Exportar datos', 'Export data', action: 'export'),
    SettingRow('Zona de riesgo', 'Danger zone',
        descEs: 'Eliminar cuenta y datos.', descEn: 'Delete account and data.',
        action: 'delete', danger: true),
  ]),
];
