class TokenPair {
  TokenPair({required this.accessToken, required this.refreshToken, required this.tokenType, required this.expiresIn});

  final String accessToken;
  final String refreshToken;
  final String tokenType;
  final int expiresIn;

  factory TokenPair.fromJson(Map<String, dynamic> json) {
    return TokenPair(
      accessToken: json['access_token'] as String,
      refreshToken: json['refresh_token'] as String,
      tokenType: json['token_type'] as String,
      expiresIn: json['expires_in'] as int,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'access_token': accessToken,
      'refresh_token': refreshToken,
      'token_type': tokenType,
      'expires_in': expiresIn,
    };
  }
}

class UserProfile {
  UserProfile({required this.id, required this.email, required this.isAdmin, required this.createdAt});

  final int id;
  final String email;
  final bool isAdmin;
  final DateTime createdAt;

  factory UserProfile.fromJson(Map<String, dynamic> json) {
    return UserProfile(
      id: json['id'] as int,
      email: json['email'] as String,
      isAdmin: json['is_admin'] as bool,
      createdAt: DateTime.parse(json['created_at'] as String),
    );
  }

  Map<String, dynamic> toJson() {
    return {'id': id, 'email': email, 'is_admin': isAdmin, 'created_at': createdAt.toIso8601String()};
  }
}

class CategoryInfo {
  CategoryInfo({
    required this.id,
    required this.nameEn,
    required this.nameRu,
    required this.descriptionEn,
    required this.descriptionRu,
  });

  final String id;
  final String nameEn;
  final String nameRu;
  final String descriptionEn;
  final String descriptionRu;

  factory CategoryInfo.fromJson(Map<String, dynamic> json) {
    return CategoryInfo(
      id: json['id'] as String,
      nameEn: json['name_en'] as String,
      nameRu: json['name_ru'] as String,
      descriptionEn: json['description_en'] as String,
      descriptionRu: json['description_ru'] as String,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name_en': nameEn,
      'name_ru': nameRu,
      'description_en': descriptionEn,
      'description_ru': descriptionRu,
    };
  }
}

class HealthStatus {
  HealthStatus({
    required this.status,
    required this.database,
    required this.redis,
    required this.worker,
    required this.version,
  });

  final String status;
  final bool database;
  final bool redis;
  final bool worker;
  final String version;

  factory HealthStatus.fromJson(Map<String, dynamic> json) {
    return HealthStatus(
      status: json['status'] as String,
      database: json['database'] as bool,
      redis: json['redis'] as bool,
      worker: json['worker'] as bool,
      version: json['version'] as String,
    );
  }

  Map<String, dynamic> toJson() {
    return {'status': status, 'database': database, 'redis': redis, 'worker': worker, 'version': version};
  }
}
