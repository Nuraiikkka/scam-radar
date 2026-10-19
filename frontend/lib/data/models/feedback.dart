class AnalysisFeedback {
  AnalysisFeedback({
    required this.isCorrect,
    required this.trueCategory,
    required this.comment,
    required this.createdAt,
  });

  final bool isCorrect;
  final String? trueCategory;
  final String? comment;
  final DateTime createdAt;

  factory AnalysisFeedback.fromJson(Map<String, dynamic> json) {
    return AnalysisFeedback(
      isCorrect: json['is_correct'] as bool,
      trueCategory: json['true_category'] as String?,
      comment: json['comment'] as String?,
      createdAt: DateTime.parse(json['created_at'] as String),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'is_correct': isCorrect,
      'true_category': trueCategory,
      'comment': comment,
      'created_at': createdAt.toIso8601String(),
    };
  }
}

class FeedbackRequest {
  FeedbackRequest({required this.isCorrect, this.trueCategory, this.comment});

  final bool isCorrect;
  final String? trueCategory;
  final String? comment;

  Map<String, dynamic> toJson() {
    return {'is_correct': isCorrect, 'true_category': trueCategory, 'comment': comment};
  }
}
