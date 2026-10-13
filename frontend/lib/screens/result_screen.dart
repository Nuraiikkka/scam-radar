import 'package:flutter/material.dart';

import '../models/analysis_result.dart';

class ResultScreen extends StatelessWidget {
  const ResultScreen({super.key, required this.result});

  final AnalysisResult result;

  Color get _riskColor {
    if (result.riskScore < .34) return Colors.green;
    if (result.riskScore < .67) return Colors.orange;
    return Colors.redAccent;
  }

  String get _riskLabel {
    if (result.riskScore < .34) return 'Low risk';
    if (result.riskScore < .67) return 'Medium risk';
    return 'High risk';
  }

  @override
  Widget build(BuildContext context) {
    final score = (result.riskScore * 100).round();
    return Scaffold(
      appBar: AppBar(title: const Text('Analysis result'), backgroundColor: Colors.transparent),
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 620),
          child: ListView(
            padding: const EdgeInsets.all(24),
            children: [
              const Chip(avatar: Icon(Icons.science_outlined, size: 18), label: Text('Demo / Mock Mode')),
              const SizedBox(height: 18),
              Card(child: Padding(padding: const EdgeInsets.all(24), child: Column(children: [Text('$score%', style: TextStyle(fontSize: 52, fontWeight: FontWeight.bold, color: _riskColor)), Text(_riskLabel, style: TextStyle(fontSize: 19, color: _riskColor, fontWeight: FontWeight.w600)), const SizedBox(height: 20), ClipRRect(borderRadius: BorderRadius.circular(12), child: LinearProgressIndicator(value: result.riskScore, minHeight: 14, color: _riskColor, backgroundColor: Colors.white12)), const SizedBox(height: 14), const Text('This is a system estimate, not proof of fraud.', textAlign: TextAlign.center)]))),
              const SizedBox(height: 16),
              Card(child: ListTile(leading: const Icon(Icons.category_outlined), title: const Text('Detected category'), subtitle: Text(result.categoryLabel))),
              const SizedBox(height: 16),
              Text('Why it may be suspicious', style: Theme.of(context).textTheme.titleLarge),
              const SizedBox(height: 8),
              ...result.reasons.map((reason) => Card(child: ListTile(leading: Icon(Icons.warning_amber_rounded, color: _riskColor), title: Text(reason)))),
              const SizedBox(height: 24),
              FilledButton.icon(onPressed: () => Navigator.of(context).pop(), icon: const Icon(Icons.refresh), label: const Text('Analyze Another Video'), style: FilledButton.styleFrom(minimumSize: const Size.fromHeight(54), backgroundColor: const Color(0xFFFF7A00))),
            ],
          ),
        ),
      ),
    );
  }
}
