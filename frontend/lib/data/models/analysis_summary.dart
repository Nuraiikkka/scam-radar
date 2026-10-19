class AnalysisSummary {
  AnalysisSummary({
    required this.id,
    required this.status,
    required this.riskScore,
    required this.category,
    required this.sourceType,
    required this.sourceUrl,
    required this.originalFilename,
    required this.createdAt,
  });

  final String id;
  final String status;
  final double? riskScore;
  final String? category;
  final String sourceType;
  final String? sourceUrl;
  final String? originalFilename;
  final DateTime createdAt;

  String get title {
    if (sourceUrl != null) {
      return sourceUrl!;
    }
    return originalFilename ?? id;
  }

  factory AnalysisSummary.fromJson(Map<String, dynamic> json) {
    return AnalysisSummary(
      id: json['id'] as String,
      status: json['status'] as String,
      riskScore: (json['risk_score'] as num?)?.toDouble(),
      category: json['category'] as String?,
      sourceType: json['source_type'] as String,
      sourceUrl: json['source_url'] as String?,
      originalFilename: json['original_filename'] as String?,
      createdAt: DateTime.parse(json['created_at'] as String),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'status': status,
      'risk_score': riskScore,
      'category': category,
      'source_type': sourceType,
      'source_url': sourceUrl,
      'original_filename': originalFilename,
      'created_at': createdAt.toIso8601String(),
    };
  }
}

class AnalysisPage {
  AnalysisPage({required this.items, required this.total, required this.page, required this.pageSize});

  final List<AnalysisSummary> items;
  final int total;
  final int page;
  final int pageSize;

  factory AnalysisPage.fromJson(Map<String, dynamic> json) {
    final itemList = json['items'] as List<dynamic>;
    final items = <AnalysisSummary>[];
    for (final item in itemList) {
      items.add(AnalysisSummary.fromJson(item as Map<String, dynamic>));
    }
    return AnalysisPage(
      items: items,
      total: json['total'] as int,
      page: json['page'] as int,
      pageSize: json['page_size'] as int,
    );
  }

  Map<String, dynamic> toJson() {
    final itemList = <Map<String, dynamic>>[];
    for (final item in items) {
      itemList.add(item.toJson());
    }
    return {'items': itemList, 'total': total, 'page': page, 'page_size': pageSize};
  }
}

class AnalyzeCreated {
  AnalyzeCreated({required this.analysisId, required this.status});

  final String analysisId;
  final String status;

  factory AnalyzeCreated.fromJson(Map<String, dynamic> json) {
    return AnalyzeCreated(analysisId: json['analysis_id'] as String, status: json['status'] as String);
  }

  Map<String, dynamic> toJson() {
    return {'analysis_id': analysisId, 'status': status};
  }
}
