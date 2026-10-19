import 'package:flutter/material.dart';

class AppColors {
  static const Color brand = Color(0xFF3949AB);
  static const Color riskLow = Color(0xFF1B7F3B);
  static const Color riskMedium = Color(0xFFB26A00);
  static const Color riskHigh = Color(0xFFC62828);
  static const Color riskUnknown = Color(0xFF6B6F80);
  static const Color onRisk = Color(0xFFFFFFFF);
}

class AppSpacing {
  static const double xs = 4;
  static const double sm = 8;
  static const double md = 12;
  static const double lg = 16;
  static const double xl = 24;
  static const double xxl = 32;
}

class AppRadius {
  static const double sm = 8;
  static const double md = 12;
  static const double lg = 20;
}

class AppDurations {
  static const Duration gauge = Duration(milliseconds: 1200);
  static const Duration pollInterval = Duration(seconds: 2);
  static const Duration maxWait = Duration(minutes: 10);
}

class RiskLevel {
  static const double mediumFrom = 0.35;
  static const double highFrom = 0.7;

  static Color color(double? score) {
    if (score == null) {
      return AppColors.riskUnknown;
    }
    if (score >= highFrom) {
      return AppColors.riskHigh;
    }
    if (score >= mediumFrom) {
      return AppColors.riskMedium;
    }
    return AppColors.riskLow;
  }

  static String level(double? score) {
    if (score == null) {
      return 'unknown';
    }
    if (score >= highFrom) {
      return 'high';
    }
    if (score >= mediumFrom) {
      return 'medium';
    }
    return 'low';
  }
}
