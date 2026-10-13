import 'package:flutter/material.dart';

import 'screens/home_screen.dart';

void main() => runApp(const ScamRadarApp());

class ScamRadarApp extends StatelessWidget {
  const ScamRadarApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Scam Radar',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        brightness: Brightness.dark,
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFFFF7A00),
          brightness: Brightness.dark,
          surface: const Color(0xFF15233B),
        ),
        scaffoldBackgroundColor: const Color(0xFF081426),
        useMaterial3: true,
      ),
      home: const HomeScreen(),
    );
  }
}
