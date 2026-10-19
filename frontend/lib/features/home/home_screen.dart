import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../config/environment.dart';
import '../../data/api/api_exception.dart';
import '../../data/models/analysis_summary.dart';
import '../../l10n/app_localizations.dart';
import '../../state/device.dart';
import '../../state/providers.dart';
import '../../theme/tokens.dart';
import '../../widgets/labels.dart';
import 'shared_link.dart';

final RegExp tiktokLink = RegExp(r'^https?://([a-z]+\.)?tiktok\.com/\S+$', caseSensitive: false);

String? validateLink(AppLocalizations l10n, String? value) {
  final text = (value ?? '').trim();
  if (text.isEmpty) {
    return l10n.homeLinkEmpty;
  }
  if (!tiktokLink.hasMatch(text)) {
    return l10n.homeLinkInvalid;
  }
  return null;
}

class HomeScreen extends ConsumerStatefulWidget {
  const HomeScreen({super.key});

  @override
  ConsumerState<HomeScreen> createState() => HomeScreenState();
}

class HomeScreenState extends ConsumerState<HomeScreen> {
  final formKey = GlobalKey<FormState>();
  final linkController = TextEditingController();
  bool sending = false;
  bool fromShare = false;

  @override
  void initState() {
    super.initState();
    final shared = ref.read(sharedLinkProvider);
    if (shared != null) {
      linkController.text = shared;
      fromShare = true;
    }
  }

  @override
  void dispose() {
    linkController.dispose();
    super.dispose();
  }

  void showError(Object error) {
    final l10n = AppLocalizations.of(context);
    ScaffoldMessenger.of(context)
        .showSnackBar(SnackBar(key: const Key('home-error'), content: Text(errorMessage(l10n, error))));
  }

  Future<void> start(Future<AnalyzeCreated> Function() request) async {
    setState(() => sending = true);
    try {
      final created = await request();
      ref.read(sharedLinkProvider.notifier).clear();
      if (mounted) {
        unawaited(context.push('/progress/${created.analysisId}'));
      }
    } on ApiException catch (error) {
      if (mounted) {
        showError(error);
      }
    } finally {
      if (mounted) {
        setState(() => sending = false);
      }
    }
  }

  Future<void> checkLink() async {
    if (!formKey.currentState!.validate()) {
      return;
    }
    final url = linkController.text.trim();
    await start(() => ref.read(apiProvider).analyzeUrl(url));
  }

  void openLogin() {
    context.push('/login');
  }

  Future<void> pickFile() async {
    final l10n = AppLocalizations.of(context);
    final PickedVideo? video;
    try {
      video = await ref.read(deviceActionsProvider).pickVideo();
    } on Exception {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(l10n.homeFileUnreadable)));
      }
      return;
    }
    if (video == null || !mounted) {
      return;
    }
    if (video.size > AppEnvironment.maxUploadMb * 1024 * 1024) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          key: const Key('home-file-too-large'),
          content: Text(l10n.homeFileTooLarge(AppEnvironment.maxUploadMb)),
        ),
      );
      return;
    }
    final api = ref.read(apiProvider);
    final picked = video;
    await start(() => api.analyzeFile(fileName: picked.name, bytes: picked.bytes, path: picked.path));
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final auth = ref.watch(authProvider);
    ref.listen<String?>(sharedLinkProvider, (previous, next) {
      if (next != null) {
        linkController.text = next;
        setState(() => fromShare = true);
      }
    });
    return Scaffold(
      appBar: AppBar(title: Text(l10n.appTitle)),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(AppSpacing.xl),
          child: Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 560),
              child: Form(
                key: formKey,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Semantics(header: true, child: Text(l10n.homeTitle, style: theme.textTheme.headlineSmall)),
                    const SizedBox(height: AppSpacing.sm),
                    Text(l10n.homeSubtitle, style: theme.textTheme.bodyLarge),
                    const SizedBox(height: AppSpacing.xl),
                    if (fromShare)
                      Padding(
                        padding: const EdgeInsets.only(bottom: AppSpacing.md),
                        child: Row(
                          key: const Key('shared-link-note'),
                          children: [
                            Icon(Icons.share, size: 18, color: theme.colorScheme.primary),
                            const SizedBox(width: AppSpacing.sm),
                            Expanded(child: Text(l10n.homeSharedLink)),
                          ],
                        ),
                      ),
                    TextFormField(
                      key: const Key('home-link-field'),
                      controller: linkController,
                      keyboardType: TextInputType.url,
                      textInputAction: TextInputAction.go,
                      autocorrect: false,
                      enabled: !sending,
                      decoration: InputDecoration(
                        labelText: l10n.homeLinkLabel,
                        hintText: l10n.homeLinkHint,
                        prefixIcon: const Icon(Icons.link),
                      ),
                      validator: (value) => validateLink(l10n, value),
                      onFieldSubmitted: (_) => checkLink(),
                    ),
                    const SizedBox(height: AppSpacing.lg),
                    FilledButton.icon(
                      key: const Key('home-check-link'),
                      onPressed: sending ? null : checkLink,
                      icon: sending
                          ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))
                          : const Icon(Icons.search),
                      label: Text(sending ? l10n.homeSending : l10n.homeCheckLink),
                    ),
                    Padding(
                      padding: const EdgeInsets.symmetric(vertical: AppSpacing.lg),
                      child: Row(
                        children: [
                          const Expanded(child: Divider()),
                          Padding(
                            padding: const EdgeInsets.symmetric(horizontal: AppSpacing.md),
                            child: Text(l10n.homeOr),
                          ),
                          const Expanded(child: Divider()),
                        ],
                      ),
                    ),
                    OutlinedButton.icon(
                      key: const Key('home-pick-file'),
                      onPressed: sending ? null : pickFile,
                      icon: const Icon(Icons.upload_file),
                      label: Text(l10n.homePickFile),
                    ),
                    const SizedBox(height: AppSpacing.xxl),
                    if (!auth.loggedIn)
                      Card(
                        child: ListTile(
                          key: const Key('home-login-hint'),
                          leading: const Icon(Icons.person_outline),
                          title: Text(l10n.homeLoginHint),
                          trailing: TextButton(
                            key: const Key('home-login'),
                            onPressed: openLogin,
                            child: Text(l10n.homeLogin),
                          ),
                        ),
                      ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
