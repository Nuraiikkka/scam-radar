import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:scam_radar/data/models/analysis.dart';
import 'package:scam_radar/data/models/analysis_summary.dart';
import 'package:scam_radar/data/models/auth.dart';
import 'package:scam_radar/data/models/feedback.dart';
import 'package:scam_radar/data/models/reason.dart';
import 'package:scam_radar/data/models/stats.dart';

typedef Parse = Map<String, dynamic> Function(Map<String, dynamic> json);

final Map<String, Parse> models = {
  'AnalysisOut': (json) => Analysis.fromJson(json).toJson(),
  'AnalysisPage': (json) => AnalysisPage.fromJson(json).toJson(),
  'AnalysisSummary': (json) => AnalysisSummary.fromJson(json).toJson(),
  'AnalyzeCreated': (json) => AnalyzeCreated.fromJson(json).toJson(),
  'CategoryCount': (json) => CategoryCount.fromJson(json).toJson(),
  'DailyRisk': (json) => DailyRisk.fromJson(json).toJson(),
  'StatsOut': (json) => Stats.fromJson(json).toJson(),
  'CategoryOut': (json) => CategoryInfo.fromJson(json).toJson(),
  'FeedbackOut': (json) => AnalysisFeedback.fromJson(json).toJson(),
  'HealthOut': (json) => HealthStatus.fromJson(json).toJson(),
  'Reason': (json) => Reason.fromJson(json).toJson(),
  'TokenPair': (json) => TokenPair.fromJson(json).toJson(),
  'UserOut': (json) => UserProfile.fromJson(json).toJson(),
};

late Map<String, dynamic> schemas;

Map<String, dynamic> resolve(Map<String, dynamic> schema) {
  final ref = schema[r'$ref'] as String?;
  if (ref == null) {
    return schema;
  }
  return schemas[ref.split('/').last] as Map<String, dynamic>;
}

bool isNullable(Map<String, dynamic> property) {
  final options = property['anyOf'] as List<dynamic>?;
  if (options == null) {
    return false;
  }
  for (final option in options) {
    if ((option as Map<String, dynamic>)['type'] == 'null') {
      return true;
    }
  }
  return false;
}

Map<String, dynamic> nonNullOption(Map<String, dynamic> property) {
  final options = property['anyOf'] as List<dynamic>?;
  if (options == null) {
    return property;
  }
  for (final option in options) {
    final map = option as Map<String, dynamic>;
    if (map['type'] != 'null') {
      return map;
    }
  }
  return property;
}

Object sampleValue(Map<String, dynamic> property) {
  final schema = resolve(nonNullOption(property));
  final enumValues = schema['enum'] as List<dynamic>?;
  if (enumValues != null) {
    return enumValues.first as Object;
  }
  if (schema.containsKey('const')) {
    return schema['const'] as Object;
  }
  switch (schema['type']) {
    case 'string':
      if (schema['format'] == 'date-time') {
        return '2026-10-01T12:00:00Z';
      }
      if (schema['format'] == 'date') {
        return '2026-10-01';
      }
      return 'text';
    case 'integer':
      return 3;
    case 'number':
      return 0.5;
    case 'boolean':
      return true;
    case 'array':
      return [sampleValue(schema['items'] as Map<String, dynamic>)];
    case 'object':
      return sampleObject(schema);
  }
  throw StateError('Unsupported schema: $schema');
}

Map<String, dynamic> sampleObject(Map<String, dynamic> schema) {
  final properties = schema['properties'] as Map<String, dynamic>;
  final result = <String, dynamic>{};
  for (final entry in properties.entries) {
    result[entry.key] = sampleValue(entry.value as Map<String, dynamic>);
  }
  return result;
}

bool matchesType(Object? value, Map<String, dynamic> property) {
  if (value == null) {
    return isNullable(property);
  }
  final schema = resolve(nonNullOption(property));
  switch (schema['type']) {
    case 'string':
      return value is String;
    case 'integer':
      return value is int;
    case 'number':
      return value is num;
    case 'boolean':
      return value is bool;
    case 'array':
      return value is List;
    case 'object':
      return value is Map;
  }
  return schema.containsKey(r'$ref') || schema.containsKey('properties');
}

void main() {
  setUpAll(() {
    final file = File('test/contract/openapi.json');
    final document = jsonDecode(file.readAsStringSync()) as Map<String, dynamic>;
    schemas = (document['components'] as Map<String, dynamic>)['schemas'] as Map<String, dynamic>;
  });

  test('every response schema used by the app has a Dart model', () {
    for (final name in models.keys) {
      expect(schemas.containsKey(name), isTrue, reason: '$name is missing from the API schema');
    }
  });

  for (final name in models.keys) {
    test('$name field names and types match the API exactly', () {
      final schema = schemas[name] as Map<String, dynamic>;
      final properties = schema['properties'] as Map<String, dynamic>;
      final output = models[name]!(sampleObject(schema));
      expect(output.keys.toSet(), properties.keys.toSet(), reason: '$name fields differ');
      for (final entry in properties.entries) {
        expect(
          matchesType(output[entry.key], entry.value as Map<String, dynamic>),
          isTrue,
          reason: '$name.${entry.key} has the wrong type',
        );
      }
    });

    test('$name nullability matches the API exactly', () {
      final schema = schemas[name] as Map<String, dynamic>;
      final properties = schema['properties'] as Map<String, dynamic>;
      for (final entry in properties.entries) {
        final json = sampleObject(schema);
        json[entry.key] = null;
        if (isNullable(entry.value as Map<String, dynamic>)) {
          final output = models[name]!(json);
          expect(output[entry.key], isNull, reason: '$name.${entry.key} should accept null');
        } else {
          expect(() => models[name]!(json), throwsA(anything), reason: '$name.${entry.key} must not be nullable');
        }
      }
    });
  }

  test('FeedbackIn request body matches the API', () {
    final schema = schemas['FeedbackIn'] as Map<String, dynamic>;
    final properties = (schema['properties'] as Map<String, dynamic>).keys.toSet();
    final body = FeedbackRequest(isCorrect: false, trueCategory: 'betting', comment: 'x').toJson();
    expect(body.keys.toSet(), properties);
    for (final required in schema['required'] as List<dynamic>) {
      expect(body.containsKey(required), isTrue);
    }
  });

  test('DeletedOut has the field the app reads', () {
    final schema = schemas['DeletedOut'] as Map<String, dynamic>;
    expect((schema['properties'] as Map<String, dynamic>).keys.toSet(), {'deleted'});
  });

  test('error responses use the shared error shape', () {
    final error = resolve((schemas['ErrorOut'] as Map<String, dynamic>)['properties']['error'] as Map<String, dynamic>);
    expect((error['properties'] as Map<String, dynamic>).keys.toSet(), {'code', 'message', 'request_id'});
    expect(schemas.containsKey('HTTPValidationError'), isFalse);
  });
}
