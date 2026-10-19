import 'package:flutter/foundation.dart';

class AppEnvironment {
  static const String name = String.fromEnvironment('APP_ENV', defaultValue: 'local');
  static const String configuredApiBaseUrl = String.fromEnvironment('API_BASE_URL', defaultValue: '');
  static const String appVersion = '1.0.0';
  static const int maxUploadMb = 60;

  static bool get isProduction => name == 'prod';

  static bool get showDeveloperSettings => name != 'prod';

  static String defaultApiBaseUrl() {
    if (configuredApiBaseUrl.isNotEmpty) {
      return configuredApiBaseUrl;
    }
    if (kIsWeb) {
      return Uri.base.origin;
    }
    if (defaultTargetPlatform == TargetPlatform.android) {
      return 'http://10.0.2.2:8080';
    }
    return 'http://localhost:8080';
  }
}
