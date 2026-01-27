/**
 * Workbox Configuration for PWA
 */

module.exports = {
  globDirectory: 'dist/',
  globPatterns: [
    '**/*.{js,css,html,ico,png,svg,woff2}'
  ],
  globIgnores: [
    '**/node_modules/**/*',
    'sw.js',
    'workbox-*.js'
  ],
  swDest: 'dist/sw.js',
  swSrc: 'src/sw-template.js',

  // Don't precache files larger than 2MB
  maximumFileSizeToCacheInBytes: 2 * 1024 * 1024,

  // Runtime caching rules
  runtimeCaching: [
    // API calls - Network First
    {
      urlPattern: /^https?:\/\/.*\/api\/v1\/.*/,
      handler: 'NetworkFirst',
      options: {
        cacheName: 'api-cache',
        networkTimeoutSeconds: 10,
        expiration: {
          maxEntries: 200,
          maxAgeSeconds: 24 * 60 * 60, // 24 hours
        },
        cacheableResponse: {
          statuses: [0, 200],
        },
      },
    },
    // Images - Stale While Revalidate
    {
      urlPattern: /\.(?:png|jpg|jpeg|svg|gif|webp)$/,
      handler: 'StaleWhileRevalidate',
      options: {
        cacheName: 'images-cache',
        expiration: {
          maxEntries: 100,
          maxAgeSeconds: 7 * 24 * 60 * 60, // 7 days
        },
      },
    },
    // Fonts - Cache First
    {
      urlPattern: /\.(?:woff|woff2|ttf|eot)$/,
      handler: 'CacheFirst',
      options: {
        cacheName: 'fonts-cache',
        expiration: {
          maxEntries: 20,
          maxAgeSeconds: 30 * 24 * 60 * 60, // 30 days
        },
      },
    },
    // Google Fonts
    {
      urlPattern: /^https:\/\/fonts\.googleapis\.com/,
      handler: 'StaleWhileRevalidate',
      options: {
        cacheName: 'google-fonts-stylesheets',
      },
    },
    {
      urlPattern: /^https:\/\/fonts\.gstatic\.com/,
      handler: 'CacheFirst',
      options: {
        cacheName: 'google-fonts-webfonts',
        expiration: {
          maxEntries: 30,
          maxAgeSeconds: 365 * 24 * 60 * 60, // 1 year
        },
      },
    },
  ],
};
