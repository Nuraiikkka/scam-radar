import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:receive_sharing_intent/receive_sharing_intent.dart';

final RegExp linkInText = RegExp(r'https?://\S+', caseSensitive: false);

String? extractLink(String text) {
  final match = linkInText.firstMatch(text);
  if (match == null) {
    return null;
  }
  return match.group(0);
}

class SharedLinkNotifier extends Notifier<String?> {
  @override
  String? build() {
    return null;
  }

  void receive(String text) {
    state = extractLink(text);
  }

  void clear() {
    state = null;
  }
}

final sharedLinkProvider = NotifierProvider<SharedLinkNotifier, String?>(SharedLinkNotifier.new);

bool platformSupportsShareSheet() {
  if (kIsWeb) {
    return false;
  }
  return defaultTargetPlatform == TargetPlatform.android || defaultTargetPlatform == TargetPlatform.iOS;
}

final shareSheetEnabledProvider = Provider<bool>((ref) => platformSupportsShareSheet());

class ShareIntentListener extends ConsumerStatefulWidget {
  const ShareIntentListener({super.key, required this.router, required this.child});

  final GoRouter router;
  final Widget child;

  @override
  ConsumerState<ShareIntentListener> createState() => ShareIntentListenerState();
}

class ShareIntentListenerState extends ConsumerState<ShareIntentListener> {
  StreamSubscription<List<SharedMediaFile>>? subscription;

  @override
  void initState() {
    super.initState();
    if (!ref.read(shareSheetEnabledProvider)) {
      return;
    }
    subscription = ReceiveSharingIntent.instance.getMediaStream().listen(handle, onError: reportError);
    readInitialShare();
  }

  void reportError(Object error) {
    debugPrint('Share sheet error: $error');
  }

  Future<void> readInitialShare() async {
    try {
      final files = await ReceiveSharingIntent.instance.getInitialMedia();
      handle(files);
      await ReceiveSharingIntent.instance.reset();
    } on Exception catch (error) {
      reportError(error);
    }
  }

  void handle(List<SharedMediaFile> files) {
    for (final file in files) {
      final link = extractLink(file.path);
      if (link != null) {
        ref.read(sharedLinkProvider.notifier).receive(link);
        widget.router.go('/home');
        return;
      }
    }
  }

  @override
  void dispose() {
    subscription?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return widget.child;
  }
}
