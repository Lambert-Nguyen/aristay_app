import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:rxdart/rxdart.dart';

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
      try {
        await ApiService().registerDeviceTokenWithRetry(token);
        debugPrint('✅ Device token registered with backend');
      } catch (e) {
        debugPrint('❌ Device token registration failed: $e');
      }
    }

    // initial token
    await send(await _messaging.getToken());
    // future refreshes
    _messaging.onTokenRefresh.listen(send);
  }

  static void _wireForegroundListener() {
    FirebaseMessaging.onMessage.listen((msg) => _showLocal(msg.notification));
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

    // Fire-and-forget: mark read
    final notifId = data['notification_id'];
    if (notifId != null) unawaited(ApiService().markNotificationAsRead(notifId));

    /* Normalise payload --------------------------------------------
       We’ll inject a 'type' field so the UI can switch easily. */
    if (data.containsKey('task_id'))      data['type'] = 'task';
    else if (data.containsKey('property_id')) data['type'] = 'property';
    else if (data.containsKey('user_id'))     data['type'] = 'user';

    _navController.add(data);
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