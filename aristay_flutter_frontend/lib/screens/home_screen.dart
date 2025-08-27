import 'dart:async';
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../services/route_observer.dart';
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

class _HomeScreenState extends State<HomeScreen> with RouteAware {
  final _api = ApiService();

  bool _loading = true;
  String? _error;

  // who am I
  User? _me;
  bool get _isAdmin => _me?.isStaff == true;

  // counts (overall)
  int _total = 0;
  int _overdue = 0;

  final Map<String, int> _byStatus = {
    'pending': 0,
    'in-progress': 0,
    'completed': 0,
    'canceled': 0,
  };

  final Set<String> _justChanged = {};

  // counts (assigned to me)
  int _myTotal = 0;
  final Map<String, int> _myByStatus = {
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

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final route = ModalRoute.of(context);
    if (route != null) routeObserver.subscribe(this, route);
  }

  @override
  void dispose() {
    routeObserver.unsubscribe(this);
    _navSub?.cancel();
    super.dispose();
  }

  // When Home is shown or we return to it, refresh & highlight changes
  @override
  void didPush() => _refreshAndFlag();
  @override
  void didPopNext() => _refreshAndFlag();

  Future<void> _bootstrap() async {
    setState(() => _loading = true);
    try {
      _me = await _api.fetchCurrentUser();
      await NotificationService.hydrateUnreadCount();

      await _loadCounts(); // overall
      if (_me != null) {
        await _loadMyCounts(_me!.id); // assigned to me
      }

      _error = null;
    } catch (e) {
      _error = e.toString();
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _loadCounts() async {
    final data = await _api.fetchTaskCounts();
    _total   = (data['total'] as num).toInt();
    final by = Map<String, dynamic>.from(data['by_status'] ?? {});
    int v(String k) => (by[k] as num?)?.toInt() ?? 0;
    _byStatus['pending']     = v('pending');
    _byStatus['in-progress'] = v('in-progress');
    _byStatus['completed']   = v('completed');
    _byStatus['canceled']    = v('canceled');
    _overdue = (data['overdue'] as num?)?.toInt() ?? 0;
  }

  Future<void> _loadMyCounts(int assigneeId) async {
    // requires the small ApiService patch below
    final data = await _api.fetchTaskCounts(assignedTo: assigneeId);
    _myTotal = (data['total'] as num).toInt();
    final by = Map<String, dynamic>.from(data['by_status'] ?? {});
    int v(String k) => (by[k] as num?)?.toInt() ?? 0;
    _myByStatus['pending']     = v('pending');
    _myByStatus['in-progress'] = v('in-progress');
    _myByStatus['completed']   = v('completed');
    _myByStatus['canceled']    = v('canceled');
  }

  Future<void> _refreshAndFlag() async {
    // snapshot before
    final before = <String, int>{
      'all'       : _total,
      'pending'   : _byStatus['pending'] ?? 0,
      'inprogress': _byStatus['in-progress'] ?? 0,
      'completed' : _byStatus['completed'] ?? 0,
      'overdue'   : _overdue,
    };
    try {
      await _loadCounts();
      if (_me != null) await _loadMyCounts(_me!.id);
      await NotificationService.hydrateUnreadCount();
    } catch (_) {}
    // detect changes
    final after = <String, int>{
      'all'       : _total,
      'pending'   : _byStatus['pending'] ?? 0,
      'inprogress': _byStatus['in-progress'] ?? 0,
      'completed' : _byStatus['completed'] ?? 0,
      'overdue'   : _overdue,
    };
    final changed = after.keys.where((k) => before[k] != null && before[k] != after[k]).toSet();
    if (!mounted) return;
    setState(() => _justChanged
      ..clear()
      ..addAll(changed));
    // fade highlight
    Future.delayed(const Duration(seconds: 1), () {
      if (mounted) setState(() => _justChanged.clear());
    });
  }


  Future<void> _onRefresh() async {
        await _refreshAndFlag();
  }

  String get _greetingName {
    final u = _me;
    if (u == null) return 'there';
    final fn = (u.firstName ?? '').trim();
    final ln = (u.lastName ?? '').trim();
    if (fn.isNotEmpty && ln.isNotEmpty) return '$fn $ln';
    if (fn.isNotEmpty) return fn;
    return u.username;
  }

  void _goTasks({String? status, bool overdueOnly = false, int? assignedTo}) {
    Navigator.pushNamed(
      context,
      '/tasks',
      arguments: <String, dynamic>{
        if (status != null) 'status': status,
        if (overdueOnly) 'overdue': true,
        if (assignedTo != null) 'assignedTo': assignedTo,
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
          IconButton(
            tooltip: 'Log out',
            icon: const Icon(Icons.logout),
            onPressed: () async {
              final prefs = await SharedPreferences.getInstance();
              await prefs.remove('auth_token');
              if (!mounted) return;
              Navigator.of(context).pushNamedAndRemoveUntil('/', (r) => false);
            },
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
              'Welcome, $_greetingName 👋',
              style: theme.textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w700),
            ),
            const SizedBox(height: 6),
            Text(
              'Here’s a quick snapshot of your workspace.',
              style: theme.textTheme.bodyMedium?.copyWith(
                color: theme.colorScheme.onSurfaceVariant,
              ),
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

            // Overall
            _SectionTitle('At a glance'),
            const SizedBox(height: 8),
            _StatsGrid(
              tiles: [
                _StatTile('All', _total, Icons.all_inbox_outlined,
                    onTap: () => _goTasks(),
                    highlight: _justChanged.contains('all')),
                _StatTile('Pending', _byStatus['pending']!, Icons.pause_circle_outline,
                  onTap: () => _goTasks(status: 'pending')),
                _StatTile('Overdue', _overdue, Icons.event_busy_outlined,
                    onTap: () => _goTasks(overdueOnly: true),
                    highlight: _justChanged.contains('overdue')),
                _StatTile('In progress', _byStatus['in-progress']!, Icons.play_circle_outline,
                  onTap: () => _goTasks(status: 'in-progress')),
                _StatTile('Completed', _byStatus['completed']!, Icons.check_circle_outline,
                    onTap: () => _goTasks(status: 'completed')),
              ],
            ),

            const SizedBox(height: 16),

            // Yours
            if (_me != null) ...[
              _SectionTitle('Your tasks'),
              const SizedBox(height: 8),
              _StatsGrid(
                tiles: [
                  _StatTile('Assigned to you', _myTotal, Icons.assignment_ind_outlined,
                      onTap: () => _goTasks(assignedTo: _me!.id)),
                  _StatTile('Pending', _myByStatus['pending']!, Icons.schedule_outlined,
                      onTap: () => _goTasks(status: 'pending', assignedTo: _me!.id)),
                  _StatTile('In progress', _myByStatus['in-progress']!, Icons.playlist_add_check_circle_outlined,
                      onTap: () => _goTasks(status: 'in-progress', assignedTo: _me!.id)),
                  _StatTile('Completed', _myByStatus['completed']!, Icons.done_all,
                      onTap: () => _goTasks(status: 'completed', assignedTo: _me!.id)),
                ],
              ),
            ],

            const SizedBox(height: 16),

            // Tip / test
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
}

// ---------- UI helpers ----------

class _SectionTitle extends StatelessWidget {
  const _SectionTitle(this.text);
  final String text;
  @override
  Widget build(BuildContext context) {
    return Text(
      text,
      style: Theme.of(context)
          .textTheme
          .titleMedium
          ?.copyWith(fontWeight: FontWeight.w700),
    );
  }
}

class _StatsGrid extends StatelessWidget {
  const _StatsGrid({required this.tiles});
  final List<_StatTile> tiles;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, c) {
        final twoCols = c.maxWidth > 520;
        final children = tiles
            .map((t) => Padding(
                  padding: const EdgeInsets.only(bottom: 12),
                  child: _StatCard(
                    icon: t.icon,
                    title: t.title,
                    value: t.value,
                    onTap: t.onTap,
                    highlight: t.highlight,
                  ),
                ))
            .toList();

        if (twoCols) {
          return GridView.count(
            physics: const NeverScrollableScrollPhysics(),
            crossAxisCount: 2,
            childAspectRatio: 2.6,
            shrinkWrap: true,
            crossAxisSpacing: 12,
            mainAxisSpacing: 12,
            children: children,
          );
        }
        return Column(children: children);
      },
    );
  }
}

class _StatTile {
  const _StatTile(this.title, this.value, this.icon, {required this.onTap, this.highlight = false});
  final String title;
  final int value;
  final IconData icon;
  final VoidCallback onTap;
  final bool highlight;
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
    required this.icon,
    required this.title,
    required this.value,
    required this.onTap,
    this.highlight = false,
  });

  final IconData icon;
  final String title;
  final int value;
  final VoidCallback onTap;
  final bool highlight;

  @override
  Widget build(BuildContext context) {
    final theme  = Theme.of(context);
    final scheme = theme.colorScheme;
    final isLight = scheme.brightness == Brightness.light;

    final dotBg     = isLight ? scheme.primary.withValues(alpha: .10) : scheme.surface;
    final dotBorder = isLight ? scheme.primary.withValues(alpha: .25) : scheme.outlineVariant;
    final dotIcon   = isLight ? scheme.primary : scheme.onSurface;

    return InkWell(
      borderRadius: BorderRadius.circular(16),
      onTap: onTap,
      child: Ink(
        decoration: BoxDecoration(
          color: (highlight
                  ? scheme.primary.withValues(alpha: .10)
                  : (isLight ? scheme.surface : scheme.surfaceContainerHigh)),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: scheme.outlineVariant),
        ),
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Row(
            children: [
              Container(
                decoration: BoxDecoration(
                  color: dotBg,
                  shape: BoxShape.circle,
                  border: Border.all(color: dotBorder),
                ),
                padding: const EdgeInsets.all(10),
                child: Icon(icon, size: 22, color: dotIcon),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      style: theme.textTheme.labelLarge?.copyWith(
                        color: scheme.onSurfaceVariant,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      '$value',
                      style: theme.textTheme.headlineSmall?.copyWith(
                        color: scheme.onSurface,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                  ],
                ),
              ),
              Icon(Icons.chevron_right, color: scheme.onSurfaceVariant),
            ],
          ),
        ),
      ),
    );
  }
}