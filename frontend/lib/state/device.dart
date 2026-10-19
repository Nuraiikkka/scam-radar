import 'package:file_picker/file_picker.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:share_plus/share_plus.dart';

class PickedVideo {
  PickedVideo({required this.name, required this.size, this.bytes, this.path});

  final String name;
  final int size;
  final Uint8List? bytes;
  final String? path;
}

class DeviceActions {
  Future<PickedVideo?> pickVideo() async {
    final file = await FilePicker.pickFile(type: FileType.video);
    if (file == null) {
      return null;
    }
    final size = await file.length() ?? 0;
    if (kIsWeb || file.path == null) {
      return PickedVideo(name: file.name, size: size, bytes: await file.readAsBytes());
    }
    return PickedVideo(name: file.name, size: size, path: file.path);
  }

  Future<bool> shareText(String text, String subject) async {
    try {
      final result = await SharePlus.instance.share(ShareParams(text: text, subject: subject));
      if (result.status != ShareResultStatus.unavailable) {
        return true;
      }
    } on Exception {
      debugPrint('Share sheet is not available, copying instead');
    }
    try {
      await Clipboard.setData(ClipboardData(text: text));
    } on Exception {
      debugPrint('Clipboard is not available');
    }
    return false;
  }
}

final deviceActionsProvider = Provider<DeviceActions>((ref) => DeviceActions());
