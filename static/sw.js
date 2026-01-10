/**
 * SELA 樂透一路發 - Service Worker
 * 處理 Web Push 通知
 */

const CACHE_NAME = 'sela-lottery-v1';

// 安裝事件
self.addEventListener('install', (event) => {
    console.log('[SW] Installing...');
    self.skipWaiting();
});

// 啟動事件
self.addEventListener('activate', (event) => {
    console.log('[SW] Activated');
    event.waitUntil(clients.claim());
});

// 推播通知事件
self.addEventListener('push', (event) => {
    console.log('[SW] Push received');
    
    let data = {
        title: 'SELA 樂透一路發',
        body: '您有新的通知',
        icon: '/static/logo.jpg',
        badge: '/static/badge.png',
        url: '/dashboard'
    };
    
    try {
        if (event.data) {
            const payload = event.data.json();
            data = { ...data, ...payload };
        }
    } catch (e) {
        console.error('[SW] Error parsing push data:', e);
    }
    
    const options = {
        body: data.body,
        icon: data.icon || '/static/logo.jpg',
        badge: data.badge || '/static/badge.png',
        tag: data.tag || 'sela-notification',
        renotify: true,
        requireInteraction: false,
        vibrate: [200, 100, 200],
        data: {
            url: data.url || '/dashboard',
            timestamp: Date.now()
        },
        actions: [
            {
                action: 'open',
                title: '查看'
            },
            {
                action: 'close',
                title: '關閉'
            }
        ]
    };
    
    event.waitUntil(
        self.registration.showNotification(data.title, options)
    );
});

// 點擊通知事件
self.addEventListener('notificationclick', (event) => {
    console.log('[SW] Notification clicked');
    
    event.notification.close();
    
    const action = event.action;
    const url = event.notification.data?.url || '/dashboard';
    
    if (action === 'close') {
        return;
    }
    
    // 開啟或聚焦到對應頁面
    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true })
            .then((clientList) => {
                // 找到已開啟的視窗
                for (const client of clientList) {
                    if (client.url.includes(self.location.origin) && 'focus' in client) {
                        client.navigate(url);
                        return client.focus();
                    }
                }
                // 沒有開啟的視窗，開新視窗
                if (clients.openWindow) {
                    return clients.openWindow(url);
                }
            })
    );
});

// 關閉通知事件
self.addEventListener('notificationclose', (event) => {
    console.log('[SW] Notification closed');
});

// 訂閱變更事件
self.addEventListener('pushsubscriptionchange', (event) => {
    console.log('[SW] Push subscription changed');
    
    event.waitUntil(
        self.registration.pushManager.subscribe({
            userVisibleOnly: true,
            applicationServerKey: self.vapidPublicKey
        }).then((subscription) => {
            // 通知伺服器更新訂閱
            return fetch('/api/v1/notify/subscribe', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${self.accessToken}`
                },
                body: JSON.stringify({
                    endpoint: subscription.endpoint,
                    p256dh: btoa(String.fromCharCode(...new Uint8Array(subscription.getKey('p256dh')))),
                    auth: btoa(String.fromCharCode(...new Uint8Array(subscription.getKey('auth'))))
                })
            });
        })
    );
});
