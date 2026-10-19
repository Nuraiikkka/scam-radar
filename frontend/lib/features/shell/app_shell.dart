import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../l10n/app_localizations.dart';
import '../../state/providers.dart';
import '../../widgets/state_views.dart';

class AppShell extends ConsumerWidget {
  const AppShell({super.key, required this.navigationShell});

  final StatefulNavigationShell navigationShell;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    ref.listen<AuthState>(authProvider, (previous, next) {
      if (next.sessionExpired && previous?.sessionExpired != true) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(key: const Key('session-expired'), content: Text(l10n.errorSessionExpired)));
      }
    });
    return Scaffold(
      body: Column(
        children: [
          const SafeArea(bottom: false, child: OfflineBanner()),
          Expanded(child: navigationShell),
        ],
      ),
      bottomNavigationBar: NavigationBar(
        key: const Key('bottom-nav'),
        selectedIndex: navigationShell.currentIndex,
        onDestinationSelected: (index) {
          navigationShell.goBranch(index, initialLocation: index == navigationShell.currentIndex);
        },
        destinations: [
          NavigationDestination(key: const Key('nav-home'), icon: const Icon(Icons.search), label: l10n.navHome),
          NavigationDestination(key: const Key('nav-history'), icon: const Icon(Icons.history), label: l10n.navHistory),
          NavigationDestination(key: const Key('nav-stats'), icon: const Icon(Icons.bar_chart), label: l10n.navStats),
          NavigationDestination(
            key: const Key('nav-settings'),
            icon: const Icon(Icons.settings),
            label: l10n.navSettings,
          ),
        ],
      ),
    );
  }
}
