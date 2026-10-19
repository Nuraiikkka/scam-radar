import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../data/api/api_exception.dart';
import '../../data/models/analysis.dart';
import '../../data/models/feedback.dart';
import '../../l10n/app_localizations.dart';
import '../../state/providers.dart';
import '../../theme/tokens.dart';
import '../../widgets/labels.dart';

Future<void> showFeedbackSheet(BuildContext context, WidgetRef ref, Analysis analysis) async {
  final sent = await showModalBottomSheet<bool>(
    context: context,
    isScrollControlled: true,
    showDragHandle: true,
    builder: (context) => FeedbackSheet(analysis: analysis),
  );
  if (sent == true && context.mounted) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(key: const Key('feedback-thanks'), content: Text(AppLocalizations.of(context).feedbackThanks)),
    );
    ref.invalidate(analysisProvider(analysis.id));
  }
}

class FeedbackSheet extends ConsumerStatefulWidget {
  const FeedbackSheet({super.key, required this.analysis});

  final Analysis analysis;

  @override
  ConsumerState<FeedbackSheet> createState() => FeedbackSheetState();
}

class FeedbackSheetState extends ConsumerState<FeedbackSheet> {
  bool? isCorrect;
  String? trueCategory;
  final commentController = TextEditingController();
  bool sending = false;
  String? error;

  @override
  void dispose() {
    commentController.dispose();
    super.dispose();
  }

  bool get canSend {
    if (sending || isCorrect == null) {
      return false;
    }
    if (isCorrect == false && trueCategory == null) {
      return false;
    }
    return true;
  }

  Future<void> send() async {
    setState(() {
      sending = true;
      error = null;
    });
    final comment = commentController.text.trim();
    final request = FeedbackRequest(
      isCorrect: isCorrect!,
      trueCategory: isCorrect! ? null : trueCategory,
      comment: comment.isEmpty ? null : comment,
    );
    try {
      await ref.read(apiProvider).sendFeedback(widget.analysis.id, request);
      if (mounted) {
        Navigator.of(context).pop(true);
      }
    } on ApiException catch (caught) {
      if (mounted) {
        setState(() {
          sending = false;
          error = errorMessage(AppLocalizations.of(context), caught);
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final options = <String>[];
    for (final category in allCategories) {
      if (category != widget.analysis.category) {
        options.add(category);
      }
    }
    return Padding(
      padding: EdgeInsets.only(
        left: AppSpacing.xl,
        right: AppSpacing.xl,
        bottom: MediaQuery.of(context).viewInsets.bottom + AppSpacing.xl,
      ),
      child: SingleChildScrollView(
        child: Column(
          key: const Key('feedback-sheet'),
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(l10n.feedbackTitle, style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: AppSpacing.lg),
            RadioGroup<bool>(
              groupValue: isCorrect,
              onChanged: (value) => setState(() => isCorrect = value),
              child: Column(
                children: [
                  RadioListTile<bool>(
                    key: const Key('feedback-correct'),
                    value: true,
                    contentPadding: EdgeInsets.zero,
                    secondary: const Icon(Icons.thumb_up_outlined),
                    title: Text(l10n.feedbackCorrect),
                  ),
                  RadioListTile<bool>(
                    key: const Key('feedback-incorrect'),
                    value: false,
                    contentPadding: EdgeInsets.zero,
                    secondary: const Icon(Icons.thumb_down_outlined),
                    title: Text(l10n.feedbackIncorrect),
                  ),
                ],
              ),
            ),
            if (isCorrect == false) ...[
              const SizedBox(height: AppSpacing.lg),
              DropdownButtonFormField<String>(
                key: const Key('feedback-category'),
                isExpanded: true,
                initialValue: trueCategory,
                decoration: InputDecoration(labelText: l10n.feedbackPickCategory),
                items: [
                  for (final category in options)
                    DropdownMenuItem(value: category, child: Text(categoryLabel(l10n, category))),
                ],
                onChanged: (value) => setState(() => trueCategory = value),
              ),
            ],
            const SizedBox(height: AppSpacing.lg),
            TextField(
              key: const Key('feedback-comment'),
              controller: commentController,
              maxLength: 500,
              maxLines: 3,
              decoration: InputDecoration(labelText: l10n.feedbackComment),
            ),
            if (error != null)
              Padding(
                padding: const EdgeInsets.only(bottom: AppSpacing.md),
                child: Text(error!, style: TextStyle(color: Theme.of(context).colorScheme.error)),
              ),
            FilledButton(
              key: const Key('feedback-send'),
              onPressed: canSend ? send : null,
              child: sending
                  ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2))
                  : Text(l10n.feedbackSend),
            ),
          ],
        ),
      ),
    );
  }
}
