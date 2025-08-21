import 'dart:async';                              // ← NEW
import 'package:flutter/material.dart';

import '../services/api_service.dart';
import '../services/notification_service.dart';   // ← navStream
import '../services/navigation_service.dart';

import '../models/user.dart';

import '../widgets/unread_badge.dart';   // new import


class HomeScreen extends StatefulWidget {
  const HomeScreen({Key? key}) : super(key: key);

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  bool   _loading  = true;
  bool   _isAdmin  = false;
  String? _error;

  late final StreamSubscription<Map<String, dynamic>> _navSub;

  @override
  void initState() {
    super.initState();
    _loadCurrentUser();

    // listen for deep-links emitted by NotificationService
    _navSub = NotificationService.navStream.listen(_handlePushNav);
    
    _fetchUnread();  // ← fire-and-forget helper below
  }

  @override
  void dispose() {
    _navSub.cancel();                               // tidy up
    super.dispose();
  }

  // ────────────────────────────────────────────────────────────
  //  UI
  // ────────────────────────────────────────────────────────────
  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }
    if (_error != null) {
      return Scaffold(body: Center(child: Text('Error: $_error')));
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('Task Management'),
        actions: [
          IconButton(
            icon: const Icon(Icons.settings),
            tooltip: 'Profile', // was 'Settings'
            onPressed: () => Navigator.pushNamed(context, '/settings'),
          ),
          UnreadBadge(
            icon: const Icon(Icons.notifications),
            onTap: () => Navigator.pushNamed(context, '/notifications'),
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
                final created = await Navigator.pushNamed(context, '/create-task');
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
            if (_isAdmin) ...[
              const SizedBox(height: 16),
              ElevatedButton.icon(
                icon: const Icon(Icons.admin_panel_settings),
                label: const Text('Manage Users'),
                onPressed: () =>
                    Navigator.pushNamed(context, '/admin/users'),
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

  // ────────────────────────────────────────────────────────────
  //  Private helpers
  // ────────────────────────────────────────────────────────────
  Future<void> _loadCurrentUser() async {
    try {
      final User user = await ApiService().fetchCurrentUser();
      setState(() => _isAdmin = user.isStaff == true);
    } catch (e) {
      _error = e.toString();
    } finally {
      setState(() => _loading = false);
    }
  }

  /// React to a nav event coming from NotificationService.
  void _handlePushNav(Map<String, dynamic> data) {
    final current = navigatorKey.currentState?.widget.toString();
    final openFromInbox = current?.contains('NotificationListScreen') ?? false;

    // when already in inbox ➜ just push
    // otherwise (banner tap) ➜ pop to home first
    void go(int id) {
      if (!openFromInbox) {
        navigatorKey.currentState?.popUntil(ModalRoute.withName('/home'));
      }
      navigatorKey.currentState?.pushNamed('/task-detail', arguments: id);
    }
    switch (data['type']) {
      case 'task':
        go(int.parse(data['task_id'].toString()));
        break;
      case 'property':
        go(int.parse(data['property_id'].toString()));
        break;
      case 'user':
        final id = int.parse(data['user_id'].toString());
        navigatorKey.currentState?.pushNamed(
          '/admin/users',
          arguments: {'highlightUserId': id},
        );
        break;
      default:
        // Optional future 'url' deep-link could be handled here
        break;
    }
  }
  
  Future<void> _fetchUnread() async {
    try {
      final resp = await ApiService().fetchNotifications(unreadOnly: true);
      unreadCount.value = resp['count'] as int;
    } catch (_) {
      // swallow – don’t block the home screen
    }
  }
}
