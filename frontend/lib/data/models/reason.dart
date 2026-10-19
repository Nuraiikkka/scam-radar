class Reason {
  Reason({required this.source, required this.code, required this.messageEn, required this.messageRu});

  final String source;
  final String code;
  final String messageEn;
  final String messageRu;

  String messageFor(String languageCode) {
    if (languageCode == 'ru') {
      return messageRu;
    }
    return messageEn;
  }

  factory Reason.fromJson(Map<String, dynamic> json) {
    return Reason(
      source: json['source'] as String,
      code: json['code'] as String,
      messageEn: json['message_en'] as String,
      messageRu: json['message_ru'] as String,
    );
  }

  Map<String, dynamic> toJson() {
    return {'source': source, 'code': code, 'message_en': messageEn, 'message_ru': messageRu};
  }
}
