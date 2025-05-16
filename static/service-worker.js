// static/service-worker.js
const CACHE_NAME = 'nyaay-saathi-v1';

// Files to cache - adjust these to match your actual project structure
const filesToCache = [
  '/',
  '/static/images/logo.png',
  '/static/images/favicon.ico',
  '/static/images/app-icon.png'
  // Add any other static assets you want to cache
];

// Install event - cache assets
self.addEventListener('install', (event) => {
  self.skipWaiting(); // Ensure new service worker activates immediately
  console.log('Service Worker: Installing');
  
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('Service Worker: Caching files');
        return cache.addAll(filesToCache).catch(error => {
          console.error('Service Worker: Cache addAll failed', error);
        });
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('Service Worker: Activating');
  const cacheWhitelist = [CACHE_NAME];
  
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheWhitelist.indexOf(cacheName) === -1) {
            console.log('Service Worker: Deleting old cache', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => {
      console.log('Service Worker: Activated');
      return self.clients.claim(); // Take control of all clients
    })
  );
});

// Fetch event - serve cached content when offline
self.addEventListener('fetch', (event) => {
  // Skip cross-origin requests and API calls
  if (!event.request.url.startsWith(self.location.origin) || 
      event.request.url.includes('/api/')) {
    return;
  }
  
  // For navigations (page loads)
  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request).catch(() => {
        return caches.match('/');
      })
    );
    return;
  }
  
  // For other requests (assets, etc.)
  event.respondWith(
    caches.match(event.request)
      .then((response) => {
        // Cache hit - return the response
        if (response) {
          return response;
        }
        
        // Not in cache - fetch from network
        return fetch(event.request)
          .then((response) => {
            // Check if we received a valid response
            if (!response || response.status !== 200 || response.type !== 'basic') {
              return response;
            }
            
            // Clone the response
            const responseToCache = response.clone();
            
            // Cache the fetched response
            caches.open(CACHE_NAME)
              .then((cache) => {
                cache.put(event.request, responseToCache);
              })
              .catch(error => {
                console.error('Service Worker: Cache put failed', error);
              });
            
            return response;
          })
          .catch((error) => {
            console.error('Service Worker: Fetch failed', error);
            
            // For image requests, you could return a default image
            if (event.request.destination === 'image') {
              return caches.match('/static/images/logo.png');
            }
            
            // Just fail for other resources
            throw error;
          });
      })
  );
});

// Simple message handler for offline functionality
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'INIT_OFFLINE_DB') {
    console.log('Service Worker: Received offline data initialization request');
  }
});

// Log any errors
self.addEventListener('error', (event) => {
  console.error('Service Worker: Error', event.error);
});