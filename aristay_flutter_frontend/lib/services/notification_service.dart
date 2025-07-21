import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/foundation.dart';
import 'dart:io';

class NotificationService {
  static final FlutterLocalNotificationsPlugin _local = FlutterLocalNotificationsPlugin();
  static final FirebaseMessaging _messaging = FirebaseMessaging.instance;

  static Future<void> init() async {
    // Local notification setup
    const ios = DarwinInitializationSettings();
    const settings = InitializationSettings(iOS: ios);

    final initialized = await _local.initialize(settings);
    debugPrint('✅ Local notification initialized: $initialized');

    // Request permissions (iOS only)
    final settingsAuth = await _messaging.requestPermission();
    debugPrint('🔐 Permissions granted: ${settingsAuth.authorizationStatus == AuthorizationStatus.authorized}');

    // Simulator push won’t work – we’ll still show local as fallback
    try {
      final token = await _messaging.getToken();
      debugPrint('📲 FCM Token: $token');
    } catch (e) {
      debugPrint('⚠️ Push setup failed (expected on simulator): $e');
    }

    // Foreground messages → show local notification
    FirebaseMessaging.onMessage.listen((RemoteMessage message) {
      final notification = message.notification;
      if (notification != null) {
        _local.show(
          notification.hashCode,
          notification.title,
          notification.body,
          const NotificationDetails(iOS: DarwinNotificationDetails()),
        );
      }
    });
  }

  static Future<void> showLocalTestNotification() async {
    await _local.show(
      0,
      '🔔 Aristay Test Notification',
      'This is just a local test.',
      const NotificationDetails(iOS: DarwinNotificationDetails()),
    );
  }
}