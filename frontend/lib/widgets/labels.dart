import '../data/api/api_exception.dart';
import '../l10n/app_localizations.dart';

const List<String> allCategories = ['investment_platform', 'pyramid', 'betting', 'giveaway', 'job_offer', 'none'];

String categoryLabel(AppLocalizations l10n, String? category) {
  switch (category) {
    case 'investment_platform':
      return l10n.categoryInvestment;
    case 'pyramid':
      return l10n.categoryPyramid;
    case 'betting':
      return l10n.categoryBetting;
    case 'giveaway':
      return l10n.categoryGiveaway;
    case 'job_offer':
      return l10n.categoryJob;
    default:
      return l10n.categoryNone;
  }
}

String sourceLabel(AppLocalizations l10n, String source) {
  switch (source) {
    case 'speech':
      return l10n.sourceSpeech;
    case 'screen_text':
      return l10n.sourceScreenText;
    case 'qr':
      return l10n.sourceQr;
    case 'classifier':
      return l10n.sourceClassifier;
    default:
      return l10n.sourceRule;
  }
}

String stageLabel(AppLocalizations l10n, String stage) {
  switch (stage) {
    case 'downloading':
      return l10n.stageDownloading;
    case 'listening':
      return l10n.stageListening;
    case 'reading_screen':
      return l10n.stageReadingScreen;
    case 'scoring':
    case 'finished':
      return l10n.stageScoring;
    default:
      return l10n.stageQueued;
  }
}

String riskLabel(AppLocalizations l10n, String level) {
  switch (level) {
    case 'high':
      return l10n.riskHigh;
    case 'medium':
      return l10n.riskMedium;
    case 'low':
      return l10n.riskLow;
    default:
      return l10n.riskUnknown;
  }
}

String errorCodeMessage(AppLocalizations l10n, String code, String fallback) {
  switch (code) {
    case 'offline':
      return l10n.errorOffline;
    case 'timeout':
      return l10n.errorTimeout;
    case 'invalid_url':
      return l10n.errorInvalidUrl;
    case 'video_private':
      return l10n.errorVideoPrivate;
    case 'video_unavailable':
      return l10n.errorVideoUnavailable;
    case 'video_too_long':
      return l10n.errorVideoTooLong;
    case 'video_too_large':
      return l10n.errorVideoTooLarge;
    case 'file_too_large':
      return l10n.errorFileTooLarge;
    case 'unsupported_file_type':
    case 'unsupported_media_type':
      return l10n.errorUnsupportedFile;
    case 'invalid_video':
    case 'video_missing':
      return l10n.errorInvalidVideo;
    case 'empty_file':
      return l10n.errorEmptyFile;
    case 'rate_limited':
      return l10n.errorRateLimited;
    case 'queue_unavailable':
    case 'service_unavailable':
      return l10n.errorQueueUnavailable;
    case 'queue_timeout':
      return l10n.errorQueueTimeout;
    case 'processing_timeout':
      return l10n.errorProcessingTimeout;
    case 'download_failed':
      return l10n.errorDownloadFailed;
    case 'download_timeout':
      return l10n.errorDownloadTimeout;
    case 'invalid_credentials':
      return l10n.errorInvalidCredentials;
    case 'email_taken':
      return l10n.errorEmailTaken;
    case 'token_expired':
    case 'invalid_token':
    case 'unauthorized':
      return l10n.errorSessionExpired;
    case 'not_found':
      return l10n.errorNotFound;
    case 'internal_error':
    case 'server_error':
    case 'audio_failed':
    case 'ffmpeg_missing':
      return l10n.errorServer;
    default:
      if (fallback.isNotEmpty) {
        return fallback;
      }
      return l10n.errorGeneric;
  }
}

String errorMessage(AppLocalizations l10n, Object error) {
  if (error is ApiException) {
    return errorCodeMessage(l10n, error.code, error.message);
  }
  return l10n.errorGeneric;
}

bool isOfflineError(Object error) {
  return error is ApiException && error.isOffline;
}
