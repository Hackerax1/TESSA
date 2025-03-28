/**
 * Service Worker for Proxmox NLI
 * Handles push notifications and caching
 */

// Cache name for offline support
const CACHE_NAME = 'proxmox-nli-cache-v1';

// Files to cache for offline support
const urlsToCache = [
  '/',
  '/static/css/styles.css',
  '/static/css/mobile.css',
  '/static/js/app.js',
  '/static/TessaLogo.webp'
];

// Install event - cache assets
self.addEventListener('install', event => {
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Opened cache');
        return cache.addAll(urlsToCache);
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.filter(cacheName => {
          return cacheName !== CACHE_NAME;
        }).map(cacheName => {
          return caches.delete(cacheName);
        })
      );
    })
  );
});

// Fetch event - serve from cache if available
self.addEventListener('fetch', event => {
  // Skip for API requests
  if (event.request.url.includes('/api/') || 
      event.request.url.includes('/socket.io/')) {
    return;
  }
  
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        // Cache hit - return response
        if (response) {
          return response;
        }
        
        // Clone the request
        const fetchRequest = event.request.clone();
        
        return fetch(fetchRequest).then(response => {
          // Check if valid response
          if (!response || response.status !== 200 || response.type !== 'basic') {
            return response;
          }
          
          // Clone the response
          const responseToCache = response.clone();
          
          caches.open(CACHE_NAME)
            .then(cache => {
              cache.put(event.request, responseToCache);
            });
            
          return response;
        });
      })
  );
});

// Push event - handle incoming push notifications
self.addEventListener('push', event => {
  console.log('Push received:', event);
  
  let data = {};
  if (event.data) {
    try {
      data = event.data.json();
    } catch (e) {
      data = {
        title: 'New Notification',
        message: event.data.text(),
        icon: '/static/TessaLogo.webp'
      };
    }
  }
  
  const title = data.title || 'Proxmox NLI Notification';
  const options = {
    body: data.message || 'You have a new notification',
    icon: data.icon || '/static/TessaLogo.webp',
    badge: '/static/TessaLogo.webp',
    data: data.data || {},
    tag: data.tag || 'default',
    renotify: data.renotify || false,
    requireInteraction: data.requireInteraction || false,
    actions: data.actions || []
  };
  
  // Show the notification
  event.waitUntil(
    self.registration.showNotification(title, options)
      .then(() => {
        // Also send the notification to the client
        return self.clients.matchAll({ type: 'window' });
      })
      .then(clients => {
        if (clients && clients.length) {
          // Send to all clients
          clients.forEach(client => {
            client.postMessage({
              type: 'PUSH_NOTIFICATION',
              title: title,
              message: options.body,
              data: options.data
            });
          });
        }
      })
  );
});

// Notification click event - handle notification clicks
self.addEventListener('notificationclick', event => {
  console.log('Notification clicked:', event);
  
  event.notification.close();
  
  // Get notification data
  const data = event.notification.data;
  
  // Handle notification click
  event.waitUntil(
    self.clients.matchAll({ type: 'window' })
      .then(clients => {
        // If a window is already open, focus it
        if (clients && clients.length) {
          clients[0].focus();
          
          // Send click event to client
          clients[0].postMessage({
            type: 'NOTIFICATION_CLICK',
            notificationId: event.notification.tag,
            action: event.action,
            data: data
          });
          
          return;
        }
        
        // Otherwise open a new window
        if (data && data.url) {
          return self.clients.openWindow(data.url);
        } else {
          return self.clients.openWindow('/');
        }
      })
  );
});
