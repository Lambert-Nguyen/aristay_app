import 'package:flutter/material.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import '../services/api_service.dart';
import '../models/user.dart';

import '../services/notification_service.dart'; //REMOVE LATER

class HomeScreen extends StatefulWidget {
  const HomeScreen({Key? key}) : super(key: key);
  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  bool _loading = true;
  bool _isAdmin = false;
  String? _error;
  final FirebaseMessaging _firebaseMessaging = FirebaseMessaging.instance;
  final FlutterLocalNotificationsPlugin _localNotificationsPlugin = FlutterLocalNotificationsPlugin();

  @override
  void initState() {
    super.initState();
    _loadCurrentUser();
  }

  Future<void> _loadCurrentUser() async {
    try {
      final user = await ApiService().fetchCurrentUser();
      setState(() {
        _isAdmin = user.isStaff == true;
      });

      try {
        await setupPushNotifications(); // run but don't block UI
      } catch (e) {
        print('⚠️ Push setup failed (expected on simulator): $e');
      }
    } catch (e) {
      _error = e.toString(); // only block if user fetch fails
    } finally {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return const Scaffold(
        body: Center(child: CircularProgressIndicator()),
      );
    }
    if (_error != null) {
      return Scaffold(
        body: Center(child: Text('Error: $_error')),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('Task Management'),
        actions: [
          IconButton(
            icon: const Icon(Icons.settings),
            tooltip: 'Settings',
            onPressed: () {
              Navigator.pushNamed(context, '/settings');
            },
          ),
        ],
      ),
      body: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text('Welcome!'),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: () => Navigator.pushNamed(context, '/tasks'),
              child: const Text('View Tasks'),
            ),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: () async {
                final created =
                    await Navigator.pushNamed(context, '/create-task');
                if (created == true) {
                  Navigator.pushReplacementNamed(context, '/tasks');
                }
              },
              child: const Text('Create New Task'),
            ),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: () => Navigator.pushNamed(context, '/properties'),
              child: const Text('Manage Properties'),
            ),

            // ← only show to admins
            if (_isAdmin) ...[
              const SizedBox(height: 16),
              ElevatedButton.icon(
                icon: const Icon(Icons.admin_panel_settings),
                label: const Text('Admin Dashboard'),
                onPressed: () => Navigator.pushNamed(context, '/admin/users'),
              ),
            ],
            ElevatedButton(
              onPressed: () => NotificationService.showLocalTestNotification(),
              child: const Text('🔔 Test Local Notification'),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> setupPushNotifications() async {
    NotificationSettings settings = await _firebaseMessaging.requestPermission(
      alert: true,
      badge: true,
      sound: true,
    );

    if (settings.authorizationStatus == AuthorizationStatus.authorized) {
      print('✅ User granted push notification permission');

      // iOS-specific: initialize local notifications
      const DarwinInitializationSettings iosSettings = DarwinInitializationSettings();

      const InitializationSettings initSettings = InitializationSettings(
        iOS: iosSettings,
        android: AndroidInitializationSettings('@mipmap/ic_launcher'),
      );

      await _localNotificationsPlugin.initialize(initSettings);

      // Listen for foreground messages
      FirebaseMessaging.onMessage.listen((RemoteMessage message) {
        RemoteNotification? notification = message.notification;
        if (notification != null) {
          _localNotificationsPlugin.show(
            notification.hashCode,
            notification.title,
            notification.body,
            const NotificationDetails(
              android: AndroidNotificationDetails('default_channel', 'Default'),
              iOS: DarwinNotificationDetails(),
            ),
          );
        }
      });

      // Print FCM token (used for sending messages)
      String? token = await _firebaseMessaging.getToken();
      print('📲 FCM Token: $token');
    } else {
      print('❌ Push notification permission denied');
    }
  }
}