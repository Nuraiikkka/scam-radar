class AnalysisResult {
  const AnalysisResult({
    required this.id,
    required this.riskScore,
    required this.category,
    required this.reasons,
    this.transcript,
    this.ocrText,
    this.sourceUrl,
  });

  final int id;
  final double riskScore;
  final String category;
  final List<String> reasons;
  final String? transcript;
  final String? ocrText;
  final String? sourceUrl;

  factory AnalysisResult.fromJson(Map<String, dynamic> json) {
    return AnalysisResult(
      id: (json['id'] as num?)?.toInt() ?? 0,
      riskScore: (json['risk_score'] as num?)?.toDouble() ?? 0,
      category: json['category'] as String? ?? 'none',
      reasons: (json['reasons'] as List<dynamic>? ?? const [])
          .map((reason) => reason.toString())
          .toList(),
      transcript: json['transcript'] as String?,
      ocrText: json['ocr_text'] as String?,
      sourceUrl: json['source_url'] as String?,
    );
  }

  String get categoryLabel => switch (category) {
        'investment_platform' => 'Investment platform',
        'pyramid' => 'Financial pyramid',
        'betting' => 'Betting promotion',
        'giveaway' => 'Fake giveaway',
        'job_offer' => 'Job offer scam',
        _ => 'No scam detected',
      };
}
