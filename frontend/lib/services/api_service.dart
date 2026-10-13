import 'dart:convert';
import 'dart:typed_data';

import 'package:http/http.dart' as http;

import '../models/analysis_result.dart';

class ApiService {
  ApiService({http.Client? client}) : _client = client ?? http.Client();

  static const baseUrl = String.fromEnvironment('API_BASE');
  final http.Client _client;

  Future<AnalysisResult> analyze({
    String? url,
    Uint8List? fileBytes,
    String? fileName,
  }) async {
    if (baseUrl.isEmpty) {
      throw StateError('API_BASE is not configured.');
    }
    if (url == null && fileBytes == null) {
      throw ArgumentError('Provide a TikTok URL or an MP4 file.');
    }

    final request = http.MultipartRequest('POST', Uri.parse('$baseUrl/analyze'));
    if (url != null) request.fields['url'] = url;
    if (fileBytes != null) {
      request.files.add(http.MultipartFile.fromBytes(
        'file',
        fileBytes,
        filename: fileName ?? 'video.mp4',
      ));
    }

    final streamedResponse = await _client.send(request);
    final response = await http.Response.fromStream(streamedResponse);
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw Exception('Analysis request failed (${response.statusCode}).');
    }
    return AnalysisResult.fromJson(
      Map<String, dynamic>.from(jsonDecode(response.body) as Map),
    );
  }
}
