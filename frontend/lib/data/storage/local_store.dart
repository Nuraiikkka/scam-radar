import 'package:shared_preferences/shared_preferences.dart';
import 'package:uuid/uuid.dart';

class LocalStore {
  LocalStore(this.prefs);

  final SharedPreferences prefs;

  static const String clientIdKey = 'client_id';
  static const String accessTokenKey = 'access_token';
  static const String refreshTokenKey = 'refresh_token';
  static const String userEmailKey = 'user_email';
  static const String onboardingDoneKey = 'onboarding_done';
  static const String languageKey = 'language';
  static const String themeKey = 'theme';
  static const String serverUrlKey = 'server_url';

  String clientId() {
    final existing = prefs.getString(clientIdKey);
    if (existing != null && existing.isNotEmpty) {
      return existing;
    }
    final created = const Uuid().v4();
    prefs.setString(clientIdKey, created);
    return created;
  }

  Future<void> resetClientId() async {
    await prefs.setString(clientIdKey, const Uuid().v4());
  }

  String? get accessToken => prefs.getString(accessTokenKey);

  String? get refreshToken => prefs.getString(refreshTokenKey);

  String? get userEmail => prefs.getString(userEmailKey);

  Future<void> saveTokens(String access, String refresh) async {
    await prefs.setString(accessTokenKey, access);
    await prefs.setString(refreshTokenKey, refresh);
  }

  Future<void> saveUserEmail(String email) async {
    await prefs.setString(userEmailKey, email);
  }

  Future<void> clearSession() async {
    await prefs.remove(accessTokenKey);
    await prefs.remove(refreshTokenKey);
    await prefs.remove(userEmailKey);
  }

  bool get onboardingDone => prefs.getBool(onboardingDoneKey) ?? false;

  Future<void> setOnboardingDone() async {
    await prefs.setBool(onboardingDoneKey, true);
  }

  String? get language => prefs.getString(languageKey);

  Future<void> setLanguage(String value) async {
    await prefs.setString(languageKey, value);
  }

  String get theme => prefs.getString(themeKey) ?? 'system';

  Future<void> setTheme(String value) async {
    await prefs.setString(themeKey, value);
  }

  String? get serverUrl => prefs.getString(serverUrlKey);

  Future<void> setServerUrl(String? value) async {
    if (value == null || value.isEmpty) {
      await prefs.remove(serverUrlKey);
      return;
    }
    await prefs.setString(serverUrlKey, value);
  }
}
