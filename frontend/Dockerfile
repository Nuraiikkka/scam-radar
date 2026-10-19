FROM debian:bookworm-slim AS build

ARG FLUTTER_VERSION=3.47.7
ARG APP_ENV=prod
ARG API_BASE_URL=
RUN apt-get update \
    && apt-get install -y --no-install-recommends git curl unzip xz-utils ca-certificates \
    && rm -rf /var/lib/apt/lists/*
RUN useradd --create-home --uid 1000 builder \
    && mkdir -p /opt/flutter /src \
    && chown builder:builder /opt/flutter /src
USER builder
RUN git clone --depth 1 --branch ${FLUTTER_VERSION} https://github.com/flutter/flutter.git /opt/flutter
ENV PATH="/opt/flutter/bin:${PATH}"
RUN flutter config --no-analytics && flutter precache --web
WORKDIR /src
COPY --chown=builder:builder pubspec.yaml pubspec.lock l10n.yaml analysis_options.yaml ./
COPY --chown=builder:builder lib/l10n/app_en.arb lib/l10n/app_ru.arb lib/l10n/
RUN flutter pub get
COPY --chown=builder:builder . .
RUN flutter build web --release --dart-define=APP_ENV=${APP_ENV} --dart-define=API_BASE_URL=${API_BASE_URL}

FROM nginxinc/nginx-unprivileged:1.27-alpine AS runtime

COPY docker/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /src/build/web /usr/share/nginx/html
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD wget -q -O /dev/null http://127.0.0.1:8080/healthz || exit 1
