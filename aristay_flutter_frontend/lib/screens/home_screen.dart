import 'dart:async';
import 'package:flutter/material.dart';

import '../services/api_service.dart';
import '../services/notification_service.dart';
import '../services/navigation_service.dart';
import '../widgets/unread_badge.dart';
import '../models/user.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({Key? key}) : super(key: key);

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final _api = ApiService();

  bool _loading = true;
  String? _error;
  bool _isAdmin = false;

  // counts
  int _total = 0;
  final Map<String, int> _byStatus = {
    'pending': 0,
    'in-progress': 0,
    'completed': 0,
    'canceled': 0,
  };

  StreamSubscription<Map<String, dynamic>>? _navSub;

  @override
  void initState() {
    super.initState();
    _bootstrap();
    _navSub = NotificationService.navStream.listen((data) {
      final nav = navigatorKey.currentState;
      if (nav == null) return;
      switch (data['type']) {
        case 'task':
          final id = int.tryParse('${data['task_id']}');
          if (id != null) nav.pushNamed('/task-detail', arguments: id);
          break;
        default:
          nav.pushNamed('/notifications');
      }
    });
  }

  Future<void> _bootstrap() async {
    setState(() => _loading = true);
    try {
      // current user
      final user = await _api.fetchCurrentUser();
      _isAdmin = user.isStaff == true;

      // unread badge hydrate + counts
      await NotificationService.hydrateUnreadCount();
      await _loadCounts();

      _error = null;
    } catch (e) {
      _error = e.toString();
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _loadCounts() async {
    final data = await _api.fetchTaskCounts(); // { total, by_status: {...} }
    _total = (data['total'] as num).toInt();
    final m = Map<String, int>.from(data['by_status'] as Map);
    for (final k in _byStatus.keys) {
      _byStatus[k] = m[k] ?? 0;
    }
  }

  @override
  void dispose() {
    _navSub?.cancel();
    super.dispose();
  }

  Future<void> _onRefresh() async {
    try {
      await _loadCounts();
      await NotificationService.hydrateUnreadCount();
      setState(() {});
    } catch (_) {
      // keep quiet; pull-to-refresh shouldn’t throw
    }
  }

  void _goTasks({String? status, bool overdueOnly = false}) {
    // Optionally pass initial filters to TaskList (see tiny patch below).
    Navigator.pushNamed(
      context,
      '/tasks',
      arguments: {
        if (status != null) 'status': status,
        if (overdueOnly) 'overdue': true,
      },
    );
  }

  void _goCreateTask() async {
    final created = await Navigator.pushNamed(context, '/create-task');
    if (!mounted) return;
    if (created == true) Navigator.pushNamed(context, '/tasks');
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }
    if (_error != null) {
      return Scaffold(
        appBar: AppBar(title: const Text('Task Management')),
        body: Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(_error!, textAlign: TextAlign.center),
              const SizedBox(height: 12),
              ElevatedButton.icon(
                onPressed: _bootstrap,
                icon: const Icon(Icons.refresh),
                label: const Text('Retry'),
              ),
            ],
          ),
        ),
      );
    }

    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Task Management'),
        actions: [
          IconButton(
            tooltip: 'Profile',
            icon: const Icon(Icons.settings),
            onPressed: () => Navigator.pushNamed(context, '/settings'),
          ),
          UnreadBadge(
            icon: const Icon(Icons.notifications),
            onTap: () => Navigator.pushNamed(context, '/notifications'),
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _onRefresh,
        child: ListView(
          padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
          children: [
            // Greeting
            Text(
              'Welcome 👋',
              style: theme.textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w700),
            ),
            const SizedBox(height: 8),
            Text(
              'Here’s a quick snapshot of your workspace.',
              style: theme.textTheme.bodyMedium?.copyWith(color: theme.hintColor),
            ),
            const SizedBox(height: 16),

            // Quick actions
            Card(
              elevation: 0,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
              child: Padding(
                padding: const EdgeInsets.fromLTRB(12, 12, 12, 12),
                child: Wrap(
                  spacing: 12,
                  runSpacing: 12,
                  children: [
                    _QuickAction(
                      icon: Icons.add_task,
                      label: 'Create Task',
                      onTap: _goCreateTask,
                    ),
                    _QuickAction(
                      icon: Icons.list_alt,
                      label: 'View Tasks',
                      onTap: () => _goTasks(),
                    ),
                    _QuickAction(
                      icon: Icons.apartment_outlined,
                      label: 'Properties',
                      onTap: () => Navigator.pushNamed(context, '/properties'),
                    ),
                    if (_isAdmin)
                      _QuickAction(
                        icon: Icons.admin_panel_settings,
                        label: 'Manage Users',
                        onTap: () => Navigator.pushNamed(context, '/admin/users'),
                      ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),

            // Stats grid
            Text('At a glance', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
            const SizedBox(height: 8),
            LayoutBuilder(
              builder: (context, c) {
                final twoCols = c.maxWidth > 520;
                final grid = [
                  _StatCard(
                    color: Colors.blue.shade50,
                    icon: Icons.all_inbox_outlined,
                    title: 'All',
                    value: _total,
                    onTap: () => _goTasks(),
                  ),
                  _StatCard(
                    color: Colors.orange.shade50,
                    icon: Icons.pause_circle_outline,
                    title: 'Pending',
                    value: _byStatus['pending']!,
                    onTap: () => _goTasks(status: 'pending'),
                  ),
                  _StatCard(
                    color: Colors.indigo.shade50,
                    icon: Icons.play_circle_outline,
                    title: 'In progress',
                    value: _byStatus['in-progress']!,
                    onTap: () => _goTasks(status: 'in-progress'),
                  ),
                  _StatCard(
                    color: Colors.green.shade50,
                    icon: Icons.check_circle_outline,
                    title: 'Completed',
                    value: _byStatus['completed']!,
                    onTap: () => _goTasks(status: 'completed'),
                  ),
                ];

                // An “Overdue” tile is useful; navigate to Tasks with the overdue chip.
                grid.insert(
                  2,
                  _StatCard(
                    color: Colors.red.shade50,
                    icon: Icons.event_busy_outlined,
                    title: 'Overdue',
                    value: _estimateOverdue(), // simple heuristic from counts
                    onTap: () => _goTasks(overdueOnly: true),
                  ),
                );

                if (twoCols) {
                  return GridView.count(
                    physics: const NeverScrollableScrollPhysics(),
                    crossAxisCount: 2,
                    childAspectRatio: 2.6,
                    shrinkWrap: true,
                    crossAxisSpacing: 12,
                    mainAxisSpacing: 12,
                    children: grid,
                  );
                }
                return Column(
                  children: [
                    for (final w in grid) Padding(padding: const EdgeInsets.only(bottom: 12), child: w),
                  ],
                );
              },
            ),

            const SizedBox(height: 16),

            // Tips / info card (nice place to keep your test notification)
            Card(
              elevation: 0,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
              child: ListTile(
                leading: const Icon(Icons.lightbulb_outline),
                title: const Text('Pro tip'),
                subtitle: const Text('You can test local notifications anytime.'),
                trailing: FilledButton.icon(
                  onPressed: () => NotificationService.showLocalTestNotification(),
                  icon: const Icon(Icons.notifications_active),
                  label: const Text('Test'),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  /// If you don’t compute this server-side, a soft heuristic is fine:
  /// Pending + In-progress that are overdue. Without raw counts,
  /// show a conservative lower-bound (0) and let the Task list do the real filter.
  int _estimateOverdue() {
    // If you later expose an explicit "overdue" count from the API,
    // replace this function with that field.
    return 0;
  }
}

class _QuickAction extends StatelessWidget {
  const _QuickAction({required this.icon, required this.label, required this.onTap});
  final IconData icon;
  final String label;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return OutlinedButton.icon(
      onPressed: onTap,
      icon: Icon(icon),
      label: Text(label),
      style: OutlinedButton.styleFrom(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      ),
    );
  }
}

class _StatCard extends StatelessWidget {
  const _StatCard({
    required this.color,
    required this.icon,
    required this.title,
    required this.value,
    required this.onTap,
  });

  final Color color;
  final IconData icon;
  final String title;
  final int value;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return InkWell(
      borderRadius: BorderRadius.circular(16),
      onTap: onTap,
      child: Ink(
        decoration: BoxDecoration(
          color: color,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: Colors.black12),
        ),
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Row(
            children: [
              Container(
                decoration: BoxDecoration(
                  color: Colors.white,
                  shape: BoxShape.circle,
                  boxShadow: [BoxShadow(color: Colors.black.withOpacity(.06), blurRadius: 6)],
                ),
                padding: const EdgeInsets.all(10),
                child: Icon(icon, size: 22),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(title,
                        style: theme.textTheme.labelLarge?.copyWith(color: Colors.black87)),
                    const SizedBox(height: 4),
                    Text('$value',
                        style: theme.textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w800)),
                  ],
                ),
              ),
              const Icon(Icons.chevron_right),
            ],
          ),
        ),
      ),
    );
  }
}