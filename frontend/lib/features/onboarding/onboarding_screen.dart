import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../l10n/app_localizations.dart';
import '../../state/providers.dart';
import '../../theme/tokens.dart';

class OnboardingScreen extends ConsumerStatefulWidget {
  const OnboardingScreen({super.key});

  @override
  ConsumerState<OnboardingScreen> createState() => OnboardingScreenState();
}

class OnboardingScreenState extends ConsumerState<OnboardingScreen> {
  final PageController controller = PageController();
  int page = 0;

  @override
  void dispose() {
    controller.dispose();
    super.dispose();
  }

  Future<void> finish() async {
    await ref.read(settingsProvider.notifier).finishOnboarding();
    if (mounted) {
      context.go('/home');
    }
  }

  void next() {
    controller.nextPage(duration: const Duration(milliseconds: 300), curve: Curves.easeOut);
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final pages = [
      OnboardingPage(icon: Icons.video_library_outlined, title: l10n.onboardingTitle1, body: l10n.onboardingBody1),
      OnboardingPage(icon: Icons.fact_check_outlined, title: l10n.onboardingTitle2, body: l10n.onboardingBody2),
      OnboardingPage(icon: Icons.gavel_outlined, title: l10n.onboardingTitle3, body: l10n.onboardingBody3),
    ];
    final isLast = page == pages.length - 1;
    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            Align(
              alignment: Alignment.centerRight,
              child: TextButton(
                key: const Key('onboarding-skip'),
                onPressed: () => controller.jumpToPage(pages.length - 1),
                child: Text(l10n.onboardingSkip),
              ),
            ),
            Expanded(
              child: PageView(
                key: const Key('onboarding-pages'),
                controller: controller,
                onPageChanged: (value) => setState(() => page = value),
                children: pages,
              ),
            ),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                for (var index = 0; index < pages.length; index++)
                  Container(
                    width: 10,
                    height: 10,
                    margin: const EdgeInsets.all(AppSpacing.xs),
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: index == page
                          ? Theme.of(context).colorScheme.primary
                          : Theme.of(context).colorScheme.outlineVariant,
                    ),
                  ),
              ],
            ),
            Padding(
              padding: const EdgeInsets.all(AppSpacing.xl),
              child: FilledButton(
                key: Key(isLast ? 'onboarding-accept' : 'onboarding-next'),
                onPressed: isLast ? finish : next,
                child: Text(isLast ? l10n.onboardingAccept : l10n.onboardingNext),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class OnboardingPage extends StatelessWidget {
  const OnboardingPage({super.key, required this.icon, required this.title, required this.body});

  final IconData icon;
  final String title;
  final String body;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return SingleChildScrollView(
      padding: const EdgeInsets.all(AppSpacing.xl),
      child: Column(
        children: [
          const SizedBox(height: AppSpacing.xxl),
          Icon(icon, size: 96, color: theme.colorScheme.primary),
          const SizedBox(height: AppSpacing.xl),
          Semantics(
            header: true,
            child: Text(title, style: theme.textTheme.headlineSmall, textAlign: TextAlign.center),
          ),
          const SizedBox(height: AppSpacing.lg),
          Text(body, style: theme.textTheme.bodyLarge, textAlign: TextAlign.center),
        ],
      ),
    );
  }
}
