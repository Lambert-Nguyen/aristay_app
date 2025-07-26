import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/foundation.dart';

import '../models/task.dart';
import 'navigation_service.dart';
import 'api_service.dart';

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

    try {
      final token = await _messaging.getToken();
      debugPrint('📲 FCM Token: $token');
    } catch (e) {
      debugPrint('⚠️ Push setup failed (expected on simulator): $e');
    }

    // Handle foreground push
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

    // Handle tapping notification when app is already open
    FirebaseMessaging.onMessageOpenedApp.listen(_handlePushNavigation);
  }

  static Future<void> getInitialMessage() async {
    final message = await _messaging.getInitialMessage();
    if (message != null) {
      await _handlePushNavigation(message);
    }
  }

  static Future<void> _handlePushNavigation(RemoteMessage message) async {
    final data = message.data;
    final taskId = data['task_id'];
    final notifId = data['notification_id'];

    if (notifId != null) {
      try {
        await ApiService().markNotificationAsRead(notifId);
        debugPrint('✅ Notification $notifId marked as read');
      } catch (e) {
        debugPrint('❌ Failed to mark notification read: $e');
      }
    }

    if (taskId != null) {
      navigatorKey.currentState?.pushNamed(
        '/task-detail',
        arguments: Task(
          id: int.parse(taskId),
          propertyId: 0,
          propertyName: 'Unknown',
          taskType: 'cleaning',
          title: 'Loading...',
          description: '',
          status: 'pending',
          createdAt: DateTime.now(),
          modifiedAt: DateTime.now(),
        ),
      );
    }
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