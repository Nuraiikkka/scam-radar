import 'dart:math';

import 'package:flutter/material.dart';

import '../l10n/app_localizations.dart';
import '../theme/tokens.dart';
import 'labels.dart';

class CategoryBadge extends StatelessWidget {
  const CategoryBadge({super.key, required this.category, required this.score});

  final String? category;
  final double? score;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final color = RiskLevel.color(score);
    return Container(
      key: const Key('category-badge'),
      padding: const EdgeInsets.symmetric(horizontal: AppSpacing.md, vertical: AppSpacing.xs + 2),
      decoration: BoxDecoration(color: color, borderRadius: BorderRadius.circular(AppRadius.lg)),
      child: Text(
        categoryLabel(l10n, category),
        style: Theme.of(context).textTheme.labelLarge?.copyWith(color: AppColors.onRisk),
      ),
    );
  }
}

class RiskGauge extends StatelessWidget {
  const RiskGauge({super.key, required this.score, this.size = 220});

  final double? score;
  final double size;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final target = (score ?? 0).clamp(0.0, 1.0);
    final level = RiskLevel.level(score);
    final percent = (target * 100).round();
    return Semantics(
      key: const Key('risk-gauge'),
      label: l10n.riskGaugeLabel(percent, riskLabel(l10n, level)),
      excludeSemantics: true,
      child: TweenAnimationBuilder<double>(
        tween: Tween(begin: 0, end: target),
        duration: AppDurations.gauge,
        curve: Curves.easeOutCubic,
        builder: (context, value, child) {
          return SizedBox(
            width: size,
            height: size * 0.62,
            child: CustomPaint(
              painter: GaugePainter(
                value: value,
                color: RiskLevel.color(score == null ? null : value),
                track: Theme.of(context).colorScheme.surfaceContainerHighest,
              ),
              child: Align(
                alignment: Alignment.bottomCenter,
                child: FittedBox(
                  fit: BoxFit.scaleDown,
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text(
                        score == null ? '—' : '${(value * 100).round()}%',
                        style: Theme.of(context).textTheme.displaySmall?.copyWith(fontWeight: FontWeight.bold),
                      ),
                      Text(riskLabel(l10n, level), style: Theme.of(context).textTheme.titleMedium),
                    ],
                  ),
                ),
              ),
            ),
          );
        },
      ),
    );
  }
}

class GaugePainter extends CustomPainter {
  GaugePainter({required this.value, required this.color, required this.track});

  final double value;
  final Color color;
  final Color track;

  @override
  void paint(Canvas canvas, Size size) {
    final stroke = size.width * 0.09;
    final rect = Rect.fromLTWH(stroke / 2, stroke / 2, size.width - stroke, size.width - stroke);
    final trackPaint = Paint();
    trackPaint.color = track;
    trackPaint.style = PaintingStyle.stroke;
    trackPaint.strokeWidth = stroke;
    trackPaint.strokeCap = StrokeCap.round;

    final valuePaint = Paint();
    valuePaint.color = color;
    valuePaint.style = PaintingStyle.stroke;
    valuePaint.strokeWidth = stroke;
    valuePaint.strokeCap = StrokeCap.round;
    canvas.drawArc(rect, pi, pi, false, trackPaint);
    if (value > 0) {
      canvas.drawArc(rect, pi, pi * value, false, valuePaint);
    }
  }

  @override
  bool shouldRepaint(GaugePainter oldDelegate) {
    return oldDelegate.value != value || oldDelegate.color != color || oldDelegate.track != track;
  }
}
