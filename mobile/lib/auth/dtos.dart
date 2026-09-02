// DTOs de auth hechos a mano (F0). El login es form-urlencoded y el refresh
// necesita leer `Set-Cookie`, cosas que el codegen no maneja bien; por eso el
// auth de F0 va manual. El resto de la API se generará del OpenAPI (F1+).

/// Respuesta de `POST /auth/login` y `POST /auth/refresh` (body).
/// Ver `backend/app/presentation/schemas/auth.py` (`AccessTokenResponse`).
class AccessTokenResponse {
  const AccessTokenResponse({required this.accessToken, required this.tokenType});

  final String accessToken;
  final String tokenType;

  factory AccessTokenResponse.fromJson(Map<String, dynamic> json) {
    return AccessTokenResponse(
      accessToken: json['access_token'] as String,
      tokenType: (json['token_type'] as String?) ?? 'bearer',
    );
  }
}

/// Respuesta de `GET /me` (ver `me.py` → `MeResponse`).
class MeResponse {
  const MeResponse({
    required this.tenantId,
    required this.userId,
    required this.role,
    required this.email,
    required this.tenantName,
    this.name,
  });

  final String tenantId;
  final String userId;
  final String role;
  final String email;
  final String tenantName;
  final String? name;

  factory MeResponse.fromJson(Map<String, dynamic> json) {
    return MeResponse(
      tenantId: json['tenant_id'] as String,
      userId: json['user_id'] as String,
      role: json['role'] as String,
      email: json['email'] as String,
      tenantName: json['tenant_name'] as String,
      name: json['name'] as String?,
    );
  }
}
