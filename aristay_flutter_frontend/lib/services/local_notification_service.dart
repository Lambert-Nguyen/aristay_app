import 'package:flutter_local_notifications/flutter_local_notifications.dart';

class LocalNotificationService {
  static final _notifications = FlutterLocalNotificationsPlugin();

  static Future<void> init() async {
    const ios = DarwinInitializationSettings();

    final success = await _notifications.initialize(
      const InitializationSettings(iOS: ios),
      onDidReceiveNotificationResponse: (response) {
        print('🔔 Notification tapped: ${response.payload}');
      },
    );

    final iosPlugin =
        _notifications.resolvePlatformSpecificImplementation<IOSFlutterLocalNotificationsPlugin>();

    final granted = await iosPlugin?.requestPermissions(
      alert: true,
      badge: true,
      sound: true,
    );

    print('✅ Local notification initialized: $success');
    print('🔐 Permissions granted: $granted');
  }

  static Future<void> showTestNotification() async {
    const details = NotificationDetails(
      iOS: DarwinNotificationDetails(),
    );

    try {
      await _notifications.show(
        0,
        '🔔 Aristay Test Notification',
        'This is just a local test.',
        details,
      );
      print('📤 Local notification triggered');
    } catch (e) {
      print('❌ Failed to show notification: $e');
    }
  }
}