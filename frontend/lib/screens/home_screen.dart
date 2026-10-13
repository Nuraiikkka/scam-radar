import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';

import '../services/mock_analysis_service.dart';
import 'result_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final _urlController = TextEditingController();
  PlatformFile? _selectedFile;
  bool _isLoading = false;
  String? _errorMessage;

  @override
  void dispose() {
    _urlController.dispose();
    super.dispose();
  }

  Future<void> _pickVideo() async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: const ['mp4'],
      withData: true,
    );
    if (result != null && result.files.isNotEmpty) {
      setState(() {
        _selectedFile = result.files.single;
        _urlController.clear();
        _errorMessage = null;
      });
    }
  }

  Future<void> _analyze() async {
    final url = _urlController.text.trim();
    if (url.isEmpty && _selectedFile == null) {
      setState(() => _errorMessage = 'Enter a TikTok link or choose an MP4 file.');
      return;
    }
    if (url.isNotEmpty && _selectedFile != null) {
      setState(() => _errorMessage = 'Choose only one source: a link or a video file.');
      return;
    }
    final uri = Uri.tryParse(url);
    if (url.isNotEmpty &&
        (uri == null ||
            !uri.hasScheme ||
            !uri.hasAuthority ||
            !uri.host.toLowerCase().endsWith('tiktok.com'))) {
      setState(() => _errorMessage = 'Enter a valid TikTok URL.');
      return;
    }

    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });
    try {
      final analysis = await MockAnalysisService().analyze(
        url: url.isEmpty ? null : url,
        fileName: _selectedFile?.name,
      );
      if (!mounted) return;
      await Navigator.of(context).push(
        MaterialPageRoute<void>(builder: (_) => ResultScreen(result: analysis)),
      );
    } catch (_) {
      if (mounted) setState(() => _errorMessage = 'Could not analyze this video. Try again.');
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final content = ConstrainedBox(
      constraints: const BoxConstraints(maxWidth: 620),
      child: Card(
        elevation: 0,
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const Text('Check before you trust', style: TextStyle(fontSize: 26, fontWeight: FontWeight.bold)),
              const SizedBox(height: 8),
              Text('Submit a TikTok link or upload an MP4. Scam Radar estimates potential fraud risk.', style: TextStyle(color: Colors.blueGrey.shade100)),
              const SizedBox(height: 24),
              TextField(
                controller: _urlController,
                enabled: _selectedFile == null && !_isLoading,
                keyboardType: TextInputType.url,
                decoration: const InputDecoration(
                  labelText: 'TikTok video URL',
                  hintText: 'https://www.tiktok.com/@...',
                  prefixIcon: Icon(Icons.link),
                  border: OutlineInputBorder(),
                ),
                onChanged: (_) => setState(() => _errorMessage = null),
              ),
              const Padding(
                padding: EdgeInsets.symmetric(vertical: 18),
                child: Row(children: [Expanded(child: Divider()), Padding(padding: EdgeInsets.symmetric(horizontal: 12), child: Text('OR')), Expanded(child: Divider())]),
              ),
              OutlinedButton.icon(
                onPressed: _isLoading || _urlController.text.isNotEmpty ? null : _pickVideo,
                icon: const Icon(Icons.upload_file),
                label: Text(_selectedFile == null ? 'Choose MP4 from device' : _selectedFile!.name),
                style: OutlinedButton.styleFrom(minimumSize: const Size.fromHeight(54)),
              ),
              if (_selectedFile != null) TextButton.icon(onPressed: _isLoading ? null : () => setState(() => _selectedFile = null), icon: const Icon(Icons.close), label: const Text('Remove selected video')),
              if (_errorMessage != null) Padding(padding: const EdgeInsets.only(top: 12), child: Text(_errorMessage!, style: const TextStyle(color: Color(0xFFFF8A80)))),
              const SizedBox(height: 20),
              FilledButton(
                onPressed: _isLoading ? null : _analyze,
                style: FilledButton.styleFrom(minimumSize: const Size.fromHeight(54), backgroundColor: const Color(0xFFFF7A00)),
                child: _isLoading ? const SizedBox(height: 22, width: 22, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white)) : const Text('Analyze Video'),
              ),
            ],
          ),
        ),
      ),
    );
    return Scaffold(
      appBar: AppBar(title: const Text('Scam Radar', style: TextStyle(fontWeight: FontWeight.bold)), backgroundColor: Colors.transparent),
      body: SafeArea(child: Center(child: SingleChildScrollView(padding: const EdgeInsets.all(24), child: Column(children: [const Chip(avatar: Icon(Icons.science_outlined, size: 18), label: Text('Demo / Mock Mode')), const SizedBox(height: 16), content, const SizedBox(height: 16), const Text('Demo results are sample data, not a verified assessment.', textAlign: TextAlign.center)])))),
    );
  }
}
