import 'dart:async';
import 'package:flutter/foundation.dart' show TargetPlatform, debugPrint, defaultTargetPlatform, kIsWeb;
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:rxdart/rxdart.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../widgets/unread_badge.dart';

import 'api_service.dart';

/// Centralised wrapper around Firebase Messaging + local notifications.
/// Exposes a [navStream] so feature screens can decide how to react to a
/// push-notification tap without tight coupling.
class NotificationService {
  // ──────────────────────────────────────────────────────────────────────
  //  Public API
  // ──────────────────────────────────────────────────────────────────────
  static Future<void> init() async {
    await _setupLocalPlugin();
    await _requestPermissionsAndPresentation();
    await _registerFcmToken();
    _wireForegroundListener();
    _wireTapListeners();
  }

  /// Delivers a map of push `data` payloads when the user taps a notification
  /// (from background / terminated / foreground).
  static Stream<Map<String, dynamic>> get navStream => _navController.stream;

  /// Tiny helper to throw a local banner manually from anywhere.
  static Future<void> showLocalTestNotification() => _showLocal(
        const RemoteNotification(
          title: '🔔 Aristay Test Notification',
          body:  'This is just a local test.',
        ),
      );

  // ──────────────────────────────────────────────────────────────────────
  //  Implementation
  // ──────────────────────────────────────────────────────────────────────
  static final _local     = FlutterLocalNotificationsPlugin();
  static final _messaging = FirebaseMessaging.instance;
  static final _navController = PublishSubject<Map<String, dynamic>>();

  static Future<void> _setupLocalPlugin() async {
    const ios     = DarwinInitializationSettings();
    const android = AndroidInitializationSettings('@mipmap/ic_launcher');
    const settings = InitializationSettings(iOS: ios, android: android);

    await _local.initialize(
      settings,
      onDidReceiveNotificationResponse: (details) {
        // If you ever add a `payload` when calling _local.show(...),
        // you can decode/forward it here.
      },
    );
  }

  static Future<void> _requestPermissionsAndPresentation() async {
    final auth = await _messaging.requestPermission();
    debugPrint('🔐 Push permission: ${auth.authorizationStatus}');
    await _messaging.setForegroundNotificationPresentationOptions(
      alert: true, badge: true, sound: true,
    );
  }

  static Future<void> _registerFcmToken() async {
    Future<void> send(String? token) async {
      if (token == null) return;

      final prefs = await SharedPreferences.getInstance();
      final auth  = prefs.getString('auth_token');

      // Not logged in yet → stash token for later.
      if (auth == null) {
        await prefs.setString('pending_fcm_token', token);
        debugPrint('ℹ️ FCM token saved to send after login');
        return;
      }

      try {
        await ApiService().registerDeviceTokenWithRetry(token);
        debugPrint('✅ Device token registered with backend');
      } catch (e) {
        debugPrint('❌ Device token registration failed: $e');
      }
    }

    try {
      // iOS: don’t call getToken() until APNs token is available.
      if (defaultTargetPlatform == TargetPlatform.iOS) {
        final apns = await _messaging.getAPNSToken();
        if (apns == null) {
          debugPrint('⏳ APNs token not ready yet; will wait for refresh.');
          _messaging.onTokenRefresh.listen(send);
          return;
        }
      }

      // Others (or iOS once APNs exists): fetch current token and send.
      await send(await _messaging.getToken());
    } catch (e) {
      // e.g. [firebase_messaging/apns-token-not-set] on simulator
      debugPrint('⚠️ getToken failed (will retry on refresh): $e');
    }

    // Always listen for future refreshes.
    _messaging.onTokenRefresh.listen(send);
  }

  static void _wireForegroundListener() {
    FirebaseMessaging.onMessage.listen((RemoteMessage msg) async {
      final n = msg.notification;
      if (defaultTargetPlatform == TargetPlatform.android || n == null) {
        final title = n?.title ?? msg.data['title'];
        final body  = n?.body  ?? msg.data['body'];
        if (title != null || body != null) {
          await _showLocal(RemoteNotification(title: title, body: body));
        }
      }
      unreadCount.value = (unreadCount.value + 1).clamp(0, 999);
    });
  }

  static void _wireTapListeners() {
    // App in background → user taps banner
    FirebaseMessaging.onMessageOpenedApp.listen(_handleTap);
    // App terminated → launched via tap
    _messaging.getInitialMessage().then((msg) {
      if (msg != null) _handleTap(msg);
    });
  }

  static Future<void> _handleTap(RemoteMessage msg) async {
    final data = Map<String, dynamic>.from(msg.data);

    // Fire-and-forget: mark read (if backend sent an id)
    final notifId = data['notification_id'];
    if (notifId != null) {
      unawaited(ApiService().markNotificationAsRead('$notifId'));
      // optimistically decrement badge
      unreadCount.value = (unreadCount.value - 1).clamp(0, 999);
    }

    // Normalise a 'type' for navigation
    if (data.containsKey('task_id'))      data['type'] = 'task';
    else if (data.containsKey('property_id')) data['type'] = 'property';
    else if (data.containsKey('user_id'))     data['type'] = 'user';

    _navController.add(data);
  }

  // Handy helper you can call after login / on app resume
  static Future<void> hydrateUnreadCount() async {
    try {
      final resp = await ApiService().fetchNotifications(unreadOnly: true);
      unreadCount.value = (resp['count'] as num).toInt();
    } catch (e) {
      debugPrint('🔕 hydrateUnreadCount failed: $e');
    }
  }

  static Future<void> registerPendingTokenIfAny() async {
    final prefs   = await SharedPreferences.getInstance();
    final pending = prefs.getString('pending_fcm_token');
    if (pending == null) return;

    try {
      await ApiService().registerDeviceTokenWithRetry(pending);
      await prefs.remove('pending_fcm_token');
      debugPrint('✅ Pending FCM token registered post-login');
    } catch (e) {
      debugPrint('❌ Failed to send pending token: $e');
    }
  }

  static Future<void> _showLocal(RemoteNotification? n) async {
    if (n == null) return;
    await _local.show(
      n.hashCode,
      n.title,
      n.body,
      const NotificationDetails(
        iOS:     DarwinNotificationDetails(),
        android: AndroidNotificationDetails(
          'default', 'Default',
          importance: Importance.high,
        ),
      ),
    );
  }
}