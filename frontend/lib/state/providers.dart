import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../config/environment.dart';
import '../data/api/api_client.dart';
import '../data/api/api_exception.dart';
import '../data/api/scam_radar_api.dart';
import '../data/models/analysis.dart';
import '../data/models/analysis_summary.dart';
import '../data/models/stats.dart';
import '../data/storage/local_store.dart';

final localStoreProvider = Provider<LocalStore>((ref) {
  throw StateError('localStoreProvider must be overridden in main() with real SharedPreferences');
});

class AppSettings {
  const AppSettings({
    required this.languageCode,
    required this.themeMode,
    required this.serverUrl,
    required this.onboardingDone,
  });

  final String? languageCode;
  final ThemeMode themeMode;
  final String serverUrl;
  final bool onboardingDone;

  AppSettings copyWith({String? languageCode, ThemeMode? themeMode, String? serverUrl, bool? onboardingDone}) {
    return AppSettings(
      languageCode: languageCode ?? this.languageCode,
      themeMode: themeMode ?? this.themeMode,
      serverUrl: serverUrl ?? this.serverUrl,
      onboardingDone: onboardingDone ?? this.onboardingDone,
    );
  }
}

ThemeMode themeFromName(String name) {
  if (name == 'light') {
    return ThemeMode.light;
  }
  if (name == 'dark') {
    return ThemeMode.dark;
  }
  return ThemeMode.system;
}

class SettingsNotifier extends Notifier<AppSettings> {
  @override
  AppSettings build() {
    final store = ref.watch(localStoreProvider);
    return AppSettings(
      languageCode: store.language,
      themeMode: themeFromName(store.theme),
      serverUrl: store.serverUrl ?? AppEnvironment.defaultApiBaseUrl(),
      onboardingDone: store.onboardingDone,
    );
  }

  LocalStore get store => ref.read(localStoreProvider);

  Future<void> setLanguage(String code) async {
    await store.setLanguage(code);
    state = state.copyWith(languageCode: code);
  }

  Future<void> setTheme(ThemeMode mode) async {
    await store.setTheme(mode.name);
    state = state.copyWith(themeMode: mode);
  }

  Future<void> setServerUrl(String? url) async {
    await store.setServerUrl(url);
    state = state.copyWith(serverUrl: url == null || url.isEmpty ? AppEnvironment.defaultApiBaseUrl() : url);
  }

  Future<void> finishOnboarding() async {
    await store.setOnboardingDone();
    state = state.copyWith(onboardingDone: true);
  }

  Future<void> showOnboardingAgain() async {
    await store.prefs.setBool(LocalStore.onboardingDoneKey, false);
    state = state.copyWith(onboardingDone: false);
  }
}

final settingsProvider = NotifierProvider<SettingsNotifier, AppSettings>(SettingsNotifier.new);

class AuthState {
  const AuthState({required this.email, this.sessionExpired = false});

  final String? email;
  final bool sessionExpired;

  bool get loggedIn => email != null;
}

class AuthNotifier extends Notifier<AuthState> {
  @override
  AuthState build() {
    final store = ref.watch(localStoreProvider);
    if (store.accessToken == null) {
      return const AuthState(email: null);
    }
    return AuthState(email: store.userEmail);
  }

  LocalStore get store => ref.read(localStoreProvider);

  Future<void> login(String email, String password) async {
    final tokens = await ref.read(apiProvider).login(email, password);
    await saveSession(tokens.accessToken, tokens.refreshToken, email);
  }

  Future<void> register(String email, String password) async {
    final tokens = await ref.read(apiProvider).register(email, password);
    await saveSession(tokens.accessToken, tokens.refreshToken, email);
  }

  Future<void> saveSession(String access, String refresh, String email) async {
    await store.saveTokens(access, refresh);
    final profile = await ref.read(apiProvider).me();
    await store.saveUserEmail(profile.email);
    state = AuthState(email: profile.email);
    ref.invalidate(historyProvider);
    ref.invalidate(statsProvider);
  }

  Future<void> logout() async {
    await store.clearSession();
    await store.resetClientId();
    state = const AuthState(email: null);
    ref.invalidate(historyProvider);
    ref.invalidate(statsProvider);
  }

  void sessionExpired() {
    state = const AuthState(email: null, sessionExpired: true);
  }
}

final authProvider = NotifierProvider<AuthNotifier, AuthState>(AuthNotifier.new);

final dioProvider = Provider<Dio>((ref) {
  final settings = ref.watch(settingsProvider);
  final store = ref.watch(localStoreProvider);

  void onSessionExpired() {
    ref.read(authProvider.notifier).sessionExpired();
  }

  return createDio(baseUrl: settings.serverUrl, store: store, onSessionExpired: onSessionExpired);
});

final apiProvider = Provider<ScamRadarApi>((ref) {
  return ScamRadarApi(ref.watch(dioProvider));
});

bool isOnline(List<ConnectivityResult> results) {
  for (final result in results) {
    if (result != ConnectivityResult.none) {
      return true;
    }
  }
  return false;
}

final connectivityProvider = StreamProvider<bool>((ref) async* {
  final connectivity = Connectivity();
  yield isOnline(await connectivity.checkConnectivity());
  await for (final results in connectivity.onConnectivityChanged) {
    yield isOnline(results);
  }
});

class HistoryState {
  const HistoryState({
    required this.items,
    required this.total,
    required this.page,
    required this.search,
    required this.category,
    this.loadingMore = false,
  });

  final List<AnalysisSummary> items;
  final int total;
  final int page;
  final String search;
  final String? category;
  final bool loadingMore;

  bool get hasMore => items.length < total;

  bool get filtered => search.isNotEmpty || category != null;
}

class HistoryNotifier extends AsyncNotifier<HistoryState> {
  String search = '';
  String? category;

  @override
  Future<HistoryState> build() async {
    return fetchFirstPage();
  }

  Future<HistoryState> fetchFirstPage() async {
    final page = await ref.read(apiProvider).listAnalyses(HistoryQuery(category: category, search: search));
    return HistoryState(items: page.items, total: page.total, page: 1, search: search, category: category);
  }

  Future<void> refresh() async {
    try {
      final firstPage = await fetchFirstPage();
      state = AsyncData(firstPage);
    } catch (error, stackTrace) {
      state = AsyncError(error, stackTrace);
    }
  }

  Future<void> setSearch(String value) async {
    search = value;
    state = const AsyncLoading<HistoryState>();
    await refresh();
  }

  Future<void> setCategory(String? value) async {
    category = value;
    state = const AsyncLoading<HistoryState>();
    await refresh();
  }

  Future<void> loadMore() async {
    final current = state.value;
    if (current == null || !current.hasMore || current.loadingMore) {
      return;
    }
    state = AsyncData(
      HistoryState(
        items: current.items,
        total: current.total,
        page: current.page,
        search: current.search,
        category: current.category,
        loadingMore: true,
      ),
    );
    final next = await ref
        .read(apiProvider)
        .listAnalyses(HistoryQuery(page: current.page + 1, category: category, search: search));
    final items = <AnalysisSummary>[];
    for (final item in current.items) {
      items.add(item);
    }
    for (final item in next.items) {
      items.add(item);
    }
    state = AsyncData(
      HistoryState(
        items: items,
        total: next.total,
        page: current.page + 1,
        search: current.search,
        category: current.category,
      ),
    );
  }

  Future<void> remove(String id) async {
    final current = state.value;
    if (current != null) {
      final items = <AnalysisSummary>[];
      for (final item in current.items) {
        if (item.id != id) {
          items.add(item);
        }
      }
      state = AsyncData(
        HistoryState(
          items: items,
          total: current.total - 1,
          page: current.page,
          search: current.search,
          category: current.category,
        ),
      );
    }
    try {
      await ref.read(apiProvider).deleteAnalysis(id);
    } on ApiException {
      await refresh();
      rethrow;
    }
    ref.invalidate(statsProvider);
  }
}

final historyProvider = AsyncNotifierProvider<HistoryNotifier, HistoryState>(HistoryNotifier.new);

final statsProvider = FutureProvider.family<Stats, String>((ref, scope) async {
  return ref.watch(apiProvider).getStats(scope: scope);
});

final analysisProvider = FutureProvider.autoDispose.family<Analysis, String>((ref, id) async {
  return ref.watch(apiProvider).getAnalysis(id);
});
