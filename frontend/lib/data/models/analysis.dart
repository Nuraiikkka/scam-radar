import 'feedback.dart';
import 'reason.dart';

class Analysis {
  Analysis({
    required this.id,
    required this.status,
    required this.stage,
    required this.riskScore,
    required this.category,
    required this.reasons,
    required this.transcript,
    required this.transcriptLanguage,
    required this.ocrText,
    required this.links,
    required this.phones,
    required this.qrCodes,
    required this.sourceType,
    required this.sourceUrl,
    required this.originalFilename,
    required this.modelVersion,
    required this.errorCode,
    required this.errorMessage,
    required this.processingSeconds,
    required this.createdAt,
    required this.finishedAt,
    required this.feedback,
  });

  final String id;
  final String status;
  final String stage;
  final double? riskScore;
  final String? category;
  final List<Reason> reasons;
  final String? transcript;
  final String? transcriptLanguage;
  final String? ocrText;
  final List<String> links;
  final List<String> phones;
  final List<String> qrCodes;
  final String sourceType;
  final String? sourceUrl;
  final String? originalFilename;
  final String? modelVersion;
  final String? errorCode;
  final String? errorMessage;
  final double? processingSeconds;
  final DateTime createdAt;
  final DateTime? finishedAt;
  final AnalysisFeedback? feedback;

  bool get isFinished => status == 'done' || status == 'failed';

  static List<String> stringList(Object? value) {
    final items = value as List<dynamic>;
    final result = <String>[];
    for (final item in items) {
      result.add(item as String);
    }
    return result;
  }

  factory Analysis.fromJson(Map<String, dynamic> json) {
    final reasonItems = json['reasons'] as List<dynamic>;
    final reasons = <Reason>[];
    for (final item in reasonItems) {
      reasons.add(Reason.fromJson(item as Map<String, dynamic>));
    }
    final feedbackJson = json['feedback'] as Map<String, dynamic>?;
    final finishedAt = json['finished_at'] as String?;
    return Analysis(
      id: json['id'] as String,
      status: json['status'] as String,
      stage: json['stage'] as String,
      riskScore: (json['risk_score'] as num?)?.toDouble(),
      category: json['category'] as String?,
      reasons: reasons,
      transcript: json['transcript'] as String?,
      transcriptLanguage: json['transcript_language'] as String?,
      ocrText: json['ocr_text'] as String?,
      links: stringList(json['links']),
      phones: stringList(json['phones']),
      qrCodes: stringList(json['qr_codes']),
      sourceType: json['source_type'] as String,
      sourceUrl: json['source_url'] as String?,
      originalFilename: json['original_filename'] as String?,
      modelVersion: json['model_version'] as String?,
      errorCode: json['error_code'] as String?,
      errorMessage: json['error_message'] as String?,
      processingSeconds: (json['processing_seconds'] as num?)?.toDouble(),
      createdAt: DateTime.parse(json['created_at'] as String),
      finishedAt: finishedAt == null ? null : DateTime.parse(finishedAt),
      feedback: feedbackJson == null ? null : AnalysisFeedback.fromJson(feedbackJson),
    );
  }

  Map<String, dynamic> toJson() {
    final reasonList = <Map<String, dynamic>>[];
    for (final reason in reasons) {
      reasonList.add(reason.toJson());
    }
    return {
      'id': id,
      'status': status,
      'stage': stage,
      'risk_score': riskScore,
      'category': category,
      'reasons': reasonList,
      'transcript': transcript,
      'transcript_language': transcriptLanguage,
      'ocr_text': ocrText,
      'links': links,
      'phones': phones,
      'qr_codes': qrCodes,
      'source_type': sourceType,
      'source_url': sourceUrl,
      'original_filename': originalFilename,
      'model_version': modelVersion,
      'error_code': errorCode,
      'error_message': errorMessage,
      'processing_seconds': processingSeconds,
      'created_at': createdAt.toIso8601String(),
      'finished_at': finishedAt?.toIso8601String(),
      'feedback': feedback?.toJson(),
    };
  }
}
