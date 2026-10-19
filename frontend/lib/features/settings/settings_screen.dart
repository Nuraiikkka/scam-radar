import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../config/environment.dart';
import '../../data/api/api_exception.dart';
import '../../l10n/app_localizations.dart';
import '../../state/providers.dart';
import '../../theme/tokens.dart';
import '../../widgets/labels.dart';
import '../../widgets/state_views.dart';

String? validateServerUrl(AppLocalizations l10n, String? value) {
  final text = (value ?? '').trim();
  final uri = Uri.tryParse(text);
  if (uri == null || !(uri.scheme == 'http' || uri.scheme == 'https') || uri.host.isEmpty) {
    return l10n.settingsServerInvalid;
  }
  return null;
}

class SettingsScreen extends ConsumerStatefulWidget {
  const SettingsScreen({super.key});

  @override
  ConsumerState<SettingsScreen> createState() => SettingsScreenState();
}

class SettingsScreenState extends ConsumerState<SettingsScreen> {
  final serverKey = GlobalKey<FormState>();
  late final TextEditingController serverController;

  @override
  void initState() {
    super.initState();
    serverController = TextEditingController(text: ref.read(settingsProvider).serverUrl);
  }

  @override
  void dispose() {
    serverController.dispose();
    super.dispose();
  }

  void toast(String text, {Key? key}) {
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(key: key, content: Text(text)));
  }

  Future<void> saveServer() async {
    if (!serverKey.currentState!.validate()) {
      return;
    }
    final l10n = AppLocalizations.of(context);
    var url = serverController.text.trim();
    while (url.endsWith('/')) {
      url = url.substring(0, url.length - 1);
    }
    await ref.read(settingsProvider.notifier).setServerUrl(url);
    ref.invalidate(historyProvider);
    ref.invalidate(statsProvider);
    toast(l10n.settingsServerSaved, key: const Key('server-saved'));
  }

  Future<void> resetServer() async {
    await ref.read(settingsProvider.notifier).setServerUrl(null);
    serverController.text = ref.read(settingsProvider).serverUrl;
    ref.invalidate(historyProvider);
    ref.invalidate(statsProvider);
  }

  Future<void> clearHistory() async {
    final l10n = AppLocalizations.of(context);
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        key: const Key('clear-history-dialog'),
        content: Text(l10n.settingsClearHistoryConfirm),
        actions: [
          TextButton(
            key: const Key('clear-history-cancel'),
            onPressed: () => Navigator.of(context).pop(false),
            child: Text(l10n.cancel),
          ),
          FilledButton(
            key: const Key('clear-history-confirm'),
            onPressed: () => Navigator.of(context).pop(true),
            child: Text(l10n.confirm),
          ),
        ],
      ),
    );
    if (confirmed != true || !mounted) {
      return;
    }
    try {
      final deleted = await ref.read(apiProvider).deleteAllAnalyses();
      ref.invalidate(historyProvider);
      ref.invalidate(statsProvider);
      toast(l10n.settingsClearHistoryDone(deleted), key: const Key('history-cleared'));
    } on ApiException catch (error) {
      toast(errorMessage(l10n, error));
    }
  }

  void openLogin() {
    context.push('/login');
  }

  Future<void> logout() async {
    final l10n = AppLocalizations.of(context);
    await ref.read(authProvider.notifier).logout();
    toast(l10n.loggedOut, key: const Key('logged-out'));
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final settings = ref.watch(settingsProvider);
    final auth = ref.watch(authProvider);
    final currentLanguage = settings.languageCode ?? Localizations.localeOf(context).languageCode;
    return Scaffold(
      appBar: AppBar(title: Text(l10n.settingsTitle)),
      body: ListView(
        key: const Key('settings-list'),
        padding: const EdgeInsets.symmetric(horizontal: AppSpacing.lg),
        children: [
          SectionTitle(l10n.settingsLanguage),
          SegmentedButton<String>(
            key: const Key('settings-language'),
            segments: [
              ButtonSegment(
                value: 'ru',
                label: Text(l10n.languageRussian, key: const Key('language-ru')),
              ),
              ButtonSegment(
                value: 'en',
                label: Text(l10n.languageEnglish, key: const Key('language-en')),
              ),
            ],
            selected: {currentLanguage == 'ru' ? 'ru' : 'en'},
            onSelectionChanged: (values) => ref.read(settingsProvider.notifier).setLanguage(values.first),
          ),
          SectionTitle(l10n.settingsTheme),
          SegmentedButton<ThemeMode>(
            key: const Key('settings-theme'),
            segments: [
              ButtonSegment(
                value: ThemeMode.system,
                label: Text(l10n.themeSystem, key: const Key('theme-system')),
              ),
              ButtonSegment(
                value: ThemeMode.light,
                label: Text(l10n.themeLight, key: const Key('theme-light')),
              ),
              ButtonSegment(
                value: ThemeMode.dark,
                label: Text(l10n.themeDark, key: const Key('theme-dark')),
              ),
            ],
            selected: {settings.themeMode},
            onSelectionChanged: (values) => ref.read(settingsProvider.notifier).setTheme(values.first),
          ),
          SectionTitle(l10n.settingsAccount),
          if (auth.loggedIn) ...[
            ListTile(
              contentPadding: EdgeInsets.zero,
              leading: const Icon(Icons.verified_user_outlined),
              title: Text(l10n.settingsLoggedInAs(auth.email!), key: const Key('settings-logged-in')),
            ),
            OutlinedButton.icon(
              key: const Key('settings-logout'),
              onPressed: logout,
              icon: const Icon(Icons.logout),
              label: Text(l10n.settingsLogout),
            ),
          ] else ...[
            Text(l10n.settingsNotLoggedIn),
            const SizedBox(height: AppSpacing.md),
            FilledButton.icon(
              key: const Key('settings-login'),
              onPressed: openLogin,
              icon: const Icon(Icons.login),
              label: Text(l10n.settingsLogin),
            ),
          ],
          SectionTitle(l10n.historyTitle),
          OutlinedButton.icon(
            key: const Key('settings-clear-history'),
            onPressed: clearHistory,
            icon: const Icon(Icons.delete_sweep_outlined),
            label: Text(l10n.settingsClearHistory),
          ),
          if (AppEnvironment.showDeveloperSettings) ...[
            SectionTitle(l10n.settingsServer),
            Form(
              key: serverKey,
              child: TextFormField(
                key: const Key('settings-server-field'),
                controller: serverController,
                keyboardType: TextInputType.url,
                autocorrect: false,
                decoration: InputDecoration(hintText: l10n.settingsServerHint, prefixIcon: const Icon(Icons.dns)),
                validator: (value) => validateServerUrl(l10n, value),
              ),
            ),
            const SizedBox(height: AppSpacing.sm),
            Row(
              children: [
                Expanded(
                  child: FilledButton(
                    key: const Key('settings-server-save'),
                    onPressed: saveServer,
                    child: Text(l10n.settingsServerSave),
                  ),
                ),
                const SizedBox(width: AppSpacing.sm),
                Expanded(
                  child: OutlinedButton(
                    key: const Key('settings-server-reset'),
                    onPressed: resetServer,
                    child: Text(l10n.settingsServerReset),
                  ),
                ),
              ],
            ),
          ],
          SectionTitle(l10n.settingsAbout),
          Text(l10n.settingsVersion(AppEnvironment.appVersion), key: const Key('settings-version')),
          const SizedBox(height: AppSpacing.sm),
          Text(l10n.onboardingBody3),
          const SizedBox(height: AppSpacing.sm),
          TextButton(
            key: const Key('settings-show-intro'),
            onPressed: () async {
              await ref.read(settingsProvider.notifier).showOnboardingAgain();
              if (context.mounted) {
                context.go('/onboarding');
              }
            },
            child: Text(l10n.settingsShowIntro),
          ),
          const SizedBox(height: AppSpacing.xxl),
        ],
      ),
    );
  }
}
