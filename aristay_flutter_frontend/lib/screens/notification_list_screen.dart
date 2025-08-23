// lib/screens/notification_list_screen.dart
import 'dart:async';
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
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


  IconData _verbIcon(String v) {
    switch (v) {
      case 'assigned':             return Icons.person_add_alt;
      case 'unassigned':           return Icons.person_remove_alt_1;
      case 'status_changed':       return Icons.sync_alt;
      case 'due_date_changed':     return Icons.event;
      case 'title_changed':        return Icons.title;
      case 'description_changed':  return Icons.description_outlined;
      case 'photo_added':          return Icons.photo;
      case 'photo_deleted':        return Icons.photo;
      case 'created':              return Icons.add_circle_outline;
      default:                     return Icons.notifications;
    }
  }

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
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: 'Refresh',
            onPressed: _loading ? null : () => _load(),
          ),
          PopupMenuButton<String>(
            onSelected: (v) {
              if (v == 'mark-all') _markAllRead();
            },
            itemBuilder: (_) => [
              PopupMenuItem<String>(
                value: 'mark-all',
                enabled: _hasUnread, // disable when nothing to do
                child: ListTile(
                  dense: true,
                  leading: Icon(Icons.done_all,
                      color: _hasUnread ? null : Colors.grey),
                  title: const Text('Mark all read'),
                ),
              ),
            ],
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
                                // Only surface this if there are unread items on device state.
                                secondaryActionLabel: _hasUnread ? 'Mark all read' : null,
                                onSecondaryAction: _hasUnread ? _markAllRead : null,
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
    if (i >= _notifs.length) {
      return const Padding(
        padding: EdgeInsets.symmetric(vertical: 16),
        child: Center(child: CircularProgressIndicator()),
      );
    }

    final n = _notifs[i];
    final title = n.taskTitle;
    final verbText = n.verb.replaceAll('_', ' ');
    final when = _relTime(n.timestamp);

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
        leading: Icon(_verbIcon(n.verb), color: n.read ? Colors.grey : Colors.blue),
        title: Text(title, maxLines: 1, overflow: TextOverflow.ellipsis),
        subtitle: Text('$verbText • $when'),
        trailing: n.read ? const SizedBox.shrink() : const Icon(Icons.brightness_1, size: 8, color: Colors.blue),
        onTap: () async {
          await _markRead(n, i);
          await Navigator.pushNamed(context, '/task-detail', arguments: n.taskId);
        },
      ),
    );
  }

  bool get _hasUnread => _notifs.any((n) => !n.read);

  Future<void> _markAllRead() async {
    try {
      await ApiService().markAllNotificationsRead();
      unreadCount.value = 0;
      setState(() {
        for (var i = 0; i < _notifs.length; i++) {
          final n = _notifs[i];
          _notifs[i] = AppNotification(
            id: n.id,
            taskId: n.taskId,
            taskTitle: n.taskTitle,
            verb: n.verb,
            read: true,
            timestamp: n.timestamp,
            readAt: DateTime.now(),
          );
        }
      });
      if (mounted) {
        ScaffoldMessenger.of(context)
          .showSnackBar(const SnackBar(content: Text('All notifications marked as read')));
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text('Failed: $e')));
      }
    }
  }
  String _relTime(DateTime t) {
    final d = DateTime.now().difference(t.toLocal());
    if (d.inSeconds < 60) return 'just now';
    if (d.inMinutes < 60) return '${d.inMinutes}m ago';
    if (d.inHours   < 24) return '${d.inHours}h ago';
    return DateFormat.yMMMd().add_jm().format(t.toLocal());
  }
}