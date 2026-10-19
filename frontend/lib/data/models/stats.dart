class CategoryCount {
  CategoryCount({required this.category, required this.count});

  final String category;
  final int count;

  factory CategoryCount.fromJson(Map<String, dynamic> json) {
    return CategoryCount(category: json['category'] as String, count: json['count'] as int);
  }

  Map<String, dynamic> toJson() {
    return {'category': category, 'count': count};
  }
}

class DailyRisk {
  DailyRisk({required this.day, required this.count, required this.averageRisk});

  final DateTime day;
  final int count;
  final double averageRisk;

  factory DailyRisk.fromJson(Map<String, dynamic> json) {
    return DailyRisk(
      day: DateTime.parse(json['day'] as String),
      count: json['count'] as int,
      averageRisk: (json['average_risk'] as num).toDouble(),
    );
  }

  Map<String, dynamic> toJson() {
    final month = day.month.toString().padLeft(2, '0');
    final date = day.day.toString().padLeft(2, '0');
    return {'day': '${day.year}-$month-$date', 'count': count, 'average_risk': averageRisk};
  }
}

class Stats {
  Stats({
    required this.totalAnalyses,
    required this.doneAnalyses,
    required this.failedAnalyses,
    required this.scamShare,
    required this.averageProcessingSeconds,
    required this.perCategory,
    required this.riskOverTime,
  });

  final int totalAnalyses;
  final int doneAnalyses;
  final int failedAnalyses;
  final double scamShare;
  final double? averageProcessingSeconds;
  final List<CategoryCount> perCategory;
  final List<DailyRisk> riskOverTime;

  factory Stats.fromJson(Map<String, dynamic> json) {
    final categories = <CategoryCount>[];
    for (final item in json['per_category'] as List<dynamic>) {
      categories.add(CategoryCount.fromJson(item as Map<String, dynamic>));
    }
    final days = <DailyRisk>[];
    for (final item in json['risk_over_time'] as List<dynamic>) {
      days.add(DailyRisk.fromJson(item as Map<String, dynamic>));
    }
    return Stats(
      totalAnalyses: json['total_analyses'] as int,
      doneAnalyses: json['done_analyses'] as int,
      failedAnalyses: json['failed_analyses'] as int,
      scamShare: (json['scam_share'] as num).toDouble(),
      averageProcessingSeconds: (json['average_processing_seconds'] as num?)?.toDouble(),
      perCategory: categories,
      riskOverTime: days,
    );
  }

  Map<String, dynamic> toJson() {
    final categories = <Map<String, dynamic>>[];
    for (final item in perCategory) {
      categories.add(item.toJson());
    }
    final days = <Map<String, dynamic>>[];
    for (final item in riskOverTime) {
      days.add(item.toJson());
    }
    return {
      'total_analyses': totalAnalyses,
      'done_analyses': doneAnalyses,
      'failed_analyses': failedAnalyses,
      'scam_share': scamShare,
      'average_processing_seconds': averageProcessingSeconds,
      'per_category': categories,
      'risk_over_time': days,
    };
  }
}
