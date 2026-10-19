import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'features/analysis/progress_screen.dart';
import 'features/analysis/result_screen.dart';
import 'features/auth/auth_screen.dart';
import 'features/history/history_screen.dart';
import 'features/home/home_screen.dart';
import 'features/home/shared_link.dart';
import 'features/onboarding/onboarding_screen.dart';
import 'features/settings/settings_screen.dart';
import 'features/shell/app_shell.dart';
import 'features/stats/stats_screen.dart';
import 'l10n/app_localizations.dart';
import 'state/providers.dart';
import 'theme/app_theme.dart';

GoRouter buildRouter(WidgetRef ref, {String initialLocation = '/home'}) {
  return GoRouter(
    initialLocation: initialLocation,
    redirect: (context, state) {
      final done = ref.read(settingsProvider).onboardingDone;
      final location = state.matchedLocation;
      if (!done && location != '/onboarding') {
        return '/onboarding';
      }
      if (location == '/') {
        return '/home';
      }
      return null;
    },
    routes: [
      GoRoute(path: '/', redirect: (context, state) => '/home'),
      GoRoute(path: '/onboarding', builder: (context, state) => const OnboardingScreen()),
      StatefulShellRoute.indexedStack(
        builder: (context, state, shell) => AppShell(navigationShell: shell),
        branches: [
          StatefulShellBranch(
            routes: [GoRoute(path: '/home', builder: (context, state) => const HomeScreen())],
          ),
          StatefulShellBranch(
            routes: [GoRoute(path: '/history', builder: (context, state) => const HistoryScreen())],
          ),
          StatefulShellBranch(
            routes: [GoRoute(path: '/stats', builder: (context, state) => const StatsScreen())],
          ),
          StatefulShellBranch(
            routes: [GoRoute(path: '/settings', builder: (context, state) => const SettingsScreen())],
          ),
        ],
      ),
      GoRoute(
        path: '/progress/:id',
        builder: (context, state) => ProgressScreen(analysisId: state.pathParameters['id']!),
      ),
      GoRoute(
        path: '/result/:id',
        builder: (context, state) => ResultScreen(analysisId: state.pathParameters['id']!),
      ),
      GoRoute(path: '/login', builder: (context, state) => const AuthScreen(registering: false)),
      GoRoute(path: '/register', builder: (context, state) => const AuthScreen(registering: true)),
    ],
  );
}

class ScamRadarApp extends ConsumerStatefulWidget {
  const ScamRadarApp({super.key, this.initialLocation = '/home'});

  final String initialLocation;

  @override
  ConsumerState<ScamRadarApp> createState() => ScamRadarAppState();
}

class ScamRadarAppState extends ConsumerState<ScamRadarApp> {
  late final GoRouter router;

  @override
  void initState() {
    super.initState();
    router = buildRouter(ref, initialLocation: widget.initialLocation);
  }

  @override
  void dispose() {
    router.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final settings = ref.watch(settingsProvider);
    final languageCode = settings.languageCode;
    return ShareIntentListener(
      router: router,
      child: MaterialApp.router(
        title: 'Scam Radar',
        debugShowCheckedModeBanner: false,
        theme: buildTheme(Brightness.light),
        darkTheme: buildTheme(Brightness.dark),
        themeMode: settings.themeMode,
        locale: languageCode == null ? null : Locale(languageCode),
        supportedLocales: AppLocalizations.supportedLocales,
        localizationsDelegates: const [
          AppLocalizations.delegate,
          GlobalMaterialLocalizations.delegate,
          GlobalWidgetsLocalizations.delegate,
          GlobalCupertinoLocalizations.delegate,
        ],
        localeResolutionCallback: (locale, supported) {
          if (locale != null && locale.languageCode == 'ru') {
            return const Locale('ru');
          }
          return const Locale('en');
        },
        routerConfig: router,
      ),
    );
  }
}
