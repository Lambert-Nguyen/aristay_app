// lib/screens/notification_list_screen.dart
import 'dart:async';
import 'package:flutter/material.dart';
import '../models/notification.dart';
import '../widgets/unread_badge.dart';
import '../widgets/empty_state.dart';

import '../services/api_service.dart';
import '../services/navigation_service.dart';

class NotificationListScreen extends StatefulWidget {
  const NotificationListScreen({super.key});

  @override
  State<NotificationListScreen> createState() => _NotificationListScreenState();
}

class _NotificationListScreenState extends State<NotificationListScreen> {
  final ScrollController _scrollCtrl = ScrollController();
  final List<AppNotification> _notifs = [];

  bool _loading = true;
  bool _loadingMore = false;
  String? _nextUrl;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
    _scrollCtrl.addListener(_onScroll);
  }

  @override
  void dispose() {
    _scrollCtrl.dispose();
    super.dispose();
  }

  void _onScroll() {
    if (_nextUrl != null &&
        !_loadingMore &&
        _scrollCtrl.position.pixels >
            0.9 * _scrollCtrl.position.maxScrollExtent) {
      _load(url: _nextUrl, append: true);
    }
  }

  Future<void> _load({String? url, bool append = false}) async {
    setState(() => append ? _loadingMore = true : _loading = true);

    try {
      final resp     = await ApiService().fetchNotifications(
                        url: url, unreadOnly: false);
      final results  = resp['results'] as List<AppNotification>;

      setState(() {
        if (append) {
          _notifs.addAll(results);
        } else {
          _notifs
            ..clear()          // ⬅️ wipe previous items
            ..addAll(results); // ⬅️ safe for any length
        }
        _nextUrl = resp['next'] as String?;
      });
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      setState(() {
        _loading     = false;
        _loadingMore = false;
      });
    }
  }

  Future<void> _markRead(AppNotification n, int index) async {
    await ApiService().markNotificationRead(n.id);
    if (!n.read) unreadCount.value = (unreadCount.value - 1).clamp(0, 999);
    setState(() => _notifs[index] = AppNotification(
          id: n.id,
          taskId: n.taskId,
          taskTitle: n.taskTitle,
          verb: n.verb,
          read: true,
          timestamp: n.timestamp,
          readAt: DateTime.now(),
        ));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Notifications'),
        actions: [
          TextButton(
            child: const Text('Mark all read', style: TextStyle(color: Colors.white)),
            onPressed: () async {
              await ApiService().markAllNotificationsRead();
              unreadCount.value = 0;
              setState(() {
                for (var i = 0; i < _notifs.length; i++) {
                  _notifs[i] = AppNotification(
                    id: _notifs[i].id,
                    taskId: _notifs[i].taskId,
                    taskTitle: _notifs[i].taskTitle,
                    verb: _notifs[i].verb,
                    read: true,
                    timestamp: _notifs[i].timestamp,
                    readAt: DateTime.now(),
                  );
                }
              });
            },
          ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Text(_error!))
              : RefreshIndicator(
                  onRefresh: () => _load(),
                  child: _notifs.isEmpty
                      ? ListView( // keep pull-to-refresh working
                          children: [
                            SizedBox(
                              height: MediaQuery.of(context).size.height * 0.7,
                              child: EmptyState(
                                title: 'Nothing to see (yet)',
                                message: 'You’ll find task updates and assignments here.',
                                illustrationAsset: 'assets/illustrations/empty_notifications.png',
                                fallbackIcon: Icons.notifications_none,
                                primaryActionLabel: 'Refresh',
                                onPrimaryAction: () => _load(),
                                secondaryActionLabel: 'Mark all read',
                                onSecondaryAction: () async {
                                  await ApiService().markAllNotificationsRead();
                                  unreadCount.value = 0;
                                  setState(() {}); // no items anyway
                                },
                              ),
                            ),
                          ],
                        )
                      : ListView.builder(
                          controller: _scrollCtrl,
                          itemCount: _notifs.length + (_loadingMore ? 1 : 0),
                          itemBuilder: _buildNotifRow, // factor out your existing builder into a method if you like
                        ),
                ),
    );
  }
  Widget _buildNotifRow(BuildContext context, int i) {
    // Footer spinner when loading more
    if (i >= _notifs.length) {
      return const Padding(
        padding: EdgeInsets.symmetric(vertical: 16),
        child: Center(child: CircularProgressIndicator()),
      );
    }

    final n = _notifs[i];
    final subtitle = '${n.verb.replaceAll("_", " ")} • ${n.taskTitle}';

    return Dismissible(
      key: ValueKey(n.id),
      direction: n.read ? DismissDirection.none : DismissDirection.endToStart,
      background: Container(
        color: Colors.green,
        alignment: Alignment.centerRight,
        padding: const EdgeInsets.only(right: 16),
        child: const Icon(Icons.done, color: Colors.white),
      ),
      onDismissed: (_) => _markRead(n, i),
      child: ListTile(
        title: Text(subtitle),
        subtitle: Text(n.timestamp.toLocal().toString().split('.').first),
        leading: Icon(
          n.read ? Icons.mark_email_read : Icons.markunread,
          color: n.read ? Colors.grey : Colors.blue,
        ),
        onTap: () async {
          // mark as read immediately for better UX
          await _markRead(n, i);
          await Navigator.pushNamed(context, '/task-detail', arguments: n.taskId);
        },
      ),
    );
  }
}