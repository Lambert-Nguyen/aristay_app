import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../widgets/task_advanced_filter_sheet.dart';
import '../widgets/empty_state.dart';
import '../models/property.dart';
import '../models/user.dart';
import '../models/task.dart';
import '../services/api_service.dart';
import 'task_search_delegate.dart';

class TaskListScreen extends StatefulWidget {
  const TaskListScreen({Key? key}) : super(key: key);
  @override
  State<TaskListScreen> createState() => _TaskListScreenState();
}

class _TaskListScreenState extends State<TaskListScreen>
    with SingleTickerProviderStateMixin {
  final _dateFmt = DateFormat.yMMMd();
  final _api = ApiService();

  // Tabs (we put "all" back here so the filter lives in one place)
  final _tabs = const ['all', 'pending', 'in-progress', 'completed', 'canceled'];
  late final TabController _tabCtrl;

  // ─── state + infinite‐scroll controller ───────────────
  List<Task> _tasks = [];
  String? _nextUrl;
  bool _isLoading = false, _isLoadingMore = false;
  String? _error;

  int _totalCount = 0;
  Map<String, int> _statusCounts = {};
  DateTime? _lastUpdated;

  String _search = '';
  String _status = 'all';

  List<Property> _properties = [];
  List<User> _assignees = [];
  int? _propertyFilter;
  int? _assigneeFilter;
  DateTime? _dateFrom;
  DateTime? _dateTo;

  bool _showOverdue = false;
  bool _initializedFromArgs = false;
  int _loadToken = 0;

  late final ScrollController _scrollCtrl;

  @override
  void initState() {
    super.initState();
    _tabCtrl = TabController(length: _tabs.length, vsync: this)
      ..addListener(_onTabChange);
    _scrollCtrl = ScrollController()
      ..addListener(() {
        final pos = _scrollCtrl.position;
        if (!_isLoadingMore && _nextUrl != null && pos.pixels >= pos.maxScrollExtent * 0.9) {
          _load(append: true);
        }
      });
    _loadFilters();
  }

  @override
  void dispose() {
    _tabCtrl.removeListener(_onTabChange);
    _tabCtrl.dispose();
    _scrollCtrl.dispose();
    super.dispose();
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (_initializedFromArgs) return;

    final args = ModalRoute.of(context)?.settings.arguments;

    // defaults
    _status = 'all';
    _showOverdue = false;
    _assigneeFilter = null;
    _search = '';
    _propertyFilter = null;
    _dateFrom = null;
    _dateTo = null;

    if (args is Map) {
      final String? status = args['status'] as String?;
      final bool overdue = (args['overdue'] as bool?) ?? false;
      final int? assignedTo = args['assignedTo'] as int?;
      if (status != null) _status = status;
      _showOverdue = overdue;
      _assigneeFilter = assignedTo;
    }

    // sync the selected tab with _status
    final idx = _tabs.indexOf(_status);
    if (idx >= 0) _tabCtrl.index = idx;

    _initializedFromArgs = true;
    _load().then((_) => _loadCounts());
  }

  // ─── data ─────────────────────────────────────────────

  Future<void> _loadFilters() async {
    final props = await _api.fetchProperties();
    final usersRes = await _api.fetchUsers();
    if (!mounted) return;
    setState(() {
      _properties = props;
      _assignees = usersRes['results'] as List<User>;
    });
  }

  Future<void> _loadCounts() async {
    try {
      final data = await _api.fetchTaskCounts();
      if (!mounted) return;
      setState(() {
        _totalCount = data['total'] as int;
        _statusCounts = Map<String, int>.from(data['by_status']);
      });
    } catch (_) {}
  }

  Future<void> _refreshAll() async {
    await _load();
    await _loadCounts();
  }

  Future<void> _load({bool append = false}) async {
    final token = ++_loadToken;
    setState(() => append ? _isLoadingMore = true : _isLoading = true);
    try {
      final Map<String, dynamic> res;
      if (append && _nextUrl != null) {
        res = await _api.fetchTasks(url: _nextUrl);
      } else {
        res = await _api.fetchTasks(
          search: _search.isEmpty ? null : _search,
          status: _status == 'all' ? null : _status,
          property: _propertyFilter,
          assignedTo: _assigneeFilter,
          dateFrom: _dateFrom,
          dateTo: _dateTo,
          overdue: _showOverdue,
        );
        _tasks = [];
      }

      if (token != _loadToken) return;

      final page = res['results'] as List<Task>;
      setState(() {
        if (append) {
          _tasks.addAll(page);
        } else {
          _tasks = page;
          _lastUpdated = DateTime.now();
        }
        _nextUrl = res['next'] as String?;
        _error = null;
      });
    } catch (e) {
      if (token != _loadToken) return;
      setState(() => _error = e.toString());
    } finally {
      if (token != _loadToken) return;
      if (!append) _loadCounts();
      setState(() {
        _isLoading = false;
        _isLoadingMore = false;
      });
    }
  }

  // ─── helpers ──────────────────────────────────────────
  void _onTabChange() {
    // ignore while animating
    if (_tabCtrl.indexIsChanging) return;
    final newStatus = _tabs[_tabCtrl.index];
    if (newStatus != _status) {
      setState(() => _status = newStatus);
      _load();
    }
  }

  int _countFor(String key) {
    if (key == 'all') return _totalCount;
    return _statusCounts[key] ?? 0;
  }

  Color _dueBg(DateTime due) {
    final now = DateTime.now();
    final d = due.toLocal();
    final overdue = d.isBefore(now);
    final days = d.difference(DateTime(now.year, now.month, now.day)).inDays;
    if (overdue) return Colors.red.shade100;
    if (days <= 2) return Colors.orange.shade100;
    return Colors.grey.shade200;
  }

  Color _dueFg(DateTime due) {
    final now = DateTime.now();
    final d = due.toLocal();
    final overdue = d.isBefore(now);
    final days = d.difference(DateTime(now.year, now.month, now.day)).inDays;
    if (overdue) return Colors.red.shade800;
    if (days <= 2) return Colors.orange.shade800;
    return Colors.grey.shade800;
  }

  String _dueLabel(DateTime due) {
    final now = DateTime.now();
    final d = due.toLocal();
    final diff = d.difference(DateTime(now.year, now.month, now.day)).inDays;
    if (d.isBefore(now)) {
      final od = DateTime(now.year, now.month, now.day)
          .difference(DateTime(d.year, d.month, d.day))
          .inDays;
      return od == 0 ? 'Overdue' : 'Overdue ${od}d';
    }
    if (diff == 0) return 'Due today';
    if (diff == 1) return 'Due tomorrow';
    return 'Due ${DateFormat.MMMd().format(d)}';
  }

  String _updatedAgo() {
    if (_lastUpdated == null) return '';
    final d = DateTime.now().difference(_lastUpdated!);
    if (d.inSeconds < 60) return 'Updated just now';
    if (d.inMinutes < 60) return 'Updated ${d.inMinutes}m ago';
    if (d.inHours < 24) return 'Updated ${d.inHours}h ago';
    return 'Updated ${DateFormat.yMMMd().add_jm().format(_lastUpdated!.toLocal())}';
  }

  void _openAdvancedFilters() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (_) => Padding(
        padding: EdgeInsets.only(bottom: MediaQuery.of(context).viewInsets.bottom),
        child: TaskAdvancedFilterSheet(
          properties: _properties,
          assignees: _assignees,
          selectedProperty: _propertyFilter,
          selectedAssignee: _assigneeFilter,
          dateFrom: _dateFrom,
          dateTo: _dateTo,
          overdue: _showOverdue,
          onApply: ({
            int? property,
            int? assignedTo,
            DateTime? dateFrom,
            DateTime? dateTo,
            bool? overdue,
          }) {
            setState(() {
              _propertyFilter = property;
              _assigneeFilter = assignedTo;
              _dateFrom = dateFrom;
              _dateTo = dateTo;
              _showOverdue = overdue ?? false;
            });
            _load();
          },
        ),
      ),
    );
  }

  bool get _hasActiveFilters =>
      _propertyFilter != null ||
      _assigneeFilter != null ||
      _dateFrom != null ||
      _dateTo != null ||
      _showOverdue ||
      _status != 'all' ||
      _search.isNotEmpty;

  // ─── UI ────────────────────────────────────────────────
  @override
  Widget build(BuildContext ctx) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(
        leading: Navigator.canPop(context)
            ? const BackButton()
            : IconButton(
                tooltip: 'Home',
                icon: const Icon(Icons.home_outlined),
                onPressed: () => Navigator.pushReplacementNamed(context, '/home'),
              ),
        title: const Text('Tasks'),
        actions: [
          if (_search.isNotEmpty)
            IconButton(
              icon: const Icon(Icons.clear),
              tooltip: 'Clear search',
              onPressed: () {
                setState(() => _search = '');
                _load();
              },
            ),
          IconButton(
            icon: const Icon(Icons.search),
            onPressed: () async {
              final result = await showSearch<String?>(
                context: context,
                delegate: TaskSearchDelegate(),
              );
              setState(() => _search = result ?? '');
              _load();
            },
          ),
          IconButton(
            icon: const Icon(Icons.filter_alt_outlined),
            tooltip: 'More filters',
            onPressed: _openAdvancedFilters,
          ),
        ],
        bottom: TabBar(
          controller: _tabCtrl,
          isScrollable: true,
          tabAlignment: TabAlignment.start,
          labelPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
          tabs: _tabs.map((k) {
            final pretty = k.replaceAll('-', ' ');
            final count = _countFor(k);
            final selected = k == _status;
            return Tab(
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                decoration: BoxDecoration(
                  color: selected
                      ? theme.colorScheme.primary.withOpacity(.12)
                      : theme.colorScheme.surfaceVariant.withOpacity(.6),
                  borderRadius: BorderRadius.circular(999),
                  border: Border.all(
                    color: selected
                        ? theme.colorScheme.primary
                        : Colors.black12,
                  ),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(
                      pretty,
                      style: theme.textTheme.bodyMedium?.copyWith(
                        fontWeight: FontWeight.w700,
                        fontSize: 15,
                      ),
                    ),
                    const SizedBox(width: 8),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(999),
                        border: Border.all(color: Colors.black12),
                      ),
                      child: Text(
                        '$count',
                        style: theme.textTheme.labelMedium,
                      ),
                    ),
                  ],
                ),
              ),
            );
          }).toList(),
        ),
      ),

      body: RefreshIndicator.adaptive(
        onRefresh: _refreshAll,
        child: _isLoading
            ? const Center(child: CircularProgressIndicator())
            : _error != null
                ? _buildError()
                : _tasks.isEmpty
                    ? _buildEmpty()
                    : _buildList(),
      ),

      floatingActionButton: FloatingActionButton(
        tooltip: 'Add Task',
        onPressed: () => Navigator.pushNamed(ctx, '/create-task').then((_) => _load()),
        child: const Icon(Icons.add),
      ),
    );
  }

  // sections

  Widget _buildError() => Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.error_outline, size: 48, color: Colors.redAccent),
            const SizedBox(height: 12),
            Text(
              'Oops! Failed to load tasks.',
              style: Theme.of(context).textTheme.titleLarge?.copyWith(
                    color: Colors.redAccent,
                    fontWeight: FontWeight.bold,
                  ),
            ),
            const SizedBox(height: 8),
            Text(_error!, textAlign: TextAlign.center),
            const SizedBox(height: 12),
            ElevatedButton(onPressed: _load, child: const Text('Retry')),
          ],
        ),
      );

  Widget _buildEmpty() {
    return EmptyState(
      title: 'No tasks found',
      message: _hasActiveFilters
          ? 'Try clearing some filters or adjust your search.'
          : 'You haven’t created any tasks yet. Tap the button below to add one.',
      illustrationAsset: 'assets/illustrations/empty_tasks.png',
      fallbackIcon: Icons.inbox,
      primaryActionLabel: 'Create a task',
      onPrimaryAction: () =>
          Navigator.pushNamed(context, '/create-task').then((_) => _load()),
      secondaryActionLabel: _hasActiveFilters ? 'Reset filters' : null,
      onSecondaryAction: _hasActiveFilters
          ? () {
              setState(() {
                _status = 'all';
                _search = '';
                _propertyFilter = null;
                _assigneeFilter = null;
                _dateFrom = null;
                _dateTo = null;
                _showOverdue = false;
              });
              _load();
            }
          : null,
    );
  }

  Widget _buildList() {
    final showFooter = _nextUrl != null;
    final itemCount = 1 + _tasks.length + (showFooter ? 1 : 0);

    return ListView.separated(
      controller: _scrollCtrl,
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      itemCount: itemCount,
      separatorBuilder: (_, __) => const SizedBox(height: 12),
      itemBuilder: (ctx, i) {
        // header
        if (i == 0) {
          final t = _updatedAgo();
          return Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              if (t.isNotEmpty)
                Padding(
                  padding: const EdgeInsets.only(left: 4, bottom: 8),
                  child: Text(t, style: const TextStyle(fontSize: 14, color: Colors.grey)),
                ),
              if (_hasActiveFilters) _activeFiltersChips(),
            ],
          );
        }

        final taskIdx = i - 1;

        // footer spinner
        if (taskIdx >= _tasks.length) {
          return Center(
            child: _isLoadingMore
                ? const Padding(
                    padding: EdgeInsets.all(12),
                    child: CircularProgressIndicator(),
                  )
                : const SizedBox.shrink(),
          );
        }

        final t = _tasks[taskIdx];
        return _TaskRow(
          task: t,
          dateFmt: _dateFmt,
          dueBg: _dueBg,
          dueFg: _dueFg,
          dueLabel: _dueLabel,
          statusBg: _statusColor(t.status),
          onTap: () async {
            final result =
                await Navigator.pushNamed(ctx, '/task-detail', arguments: t);
            if (!mounted) return;
            if (result is Task) {
              final idx = _tasks.indexWhere((x) => x.id == result.id);
              if (idx != -1) setState(() => _tasks[idx] = result);
            }
          },
        );
      },
    );
  }

  // active filter chips
  Widget _activeFiltersChips() {
    final chips = <Widget>[];

    if (_propertyFilter != null) {
      chips.add(_filterChip(
        label: _propertyName(_propertyFilter!),
        onClear: () {
          setState(() => _propertyFilter = null);
          _load();
        },
      ));
    }

    if (_assigneeFilter != null) {
      chips.add(_filterChip(
        label: _assigneeName(_assigneeFilter!),
        onClear: () {
          setState(() => _assigneeFilter = null);
          _load();
        },
      ));
    }

    if (_dateFrom != null || _dateTo != null) {
      final from = _dateFrom != null ? DateFormat.yMMMd().format(_dateFrom!) : '…';
      final to = _dateTo != null ? DateFormat.yMMMd().format(_dateTo!) : '…';
      chips.add(_filterChip(
        label: '$from → $to',
        onClear: () {
          setState(() {
            _dateFrom = null;
            _dateTo = null;
          });
          _load();
        },
      ));
    }

    if (_showOverdue) {
      chips.add(_filterChip(
        label: 'Overdue only',
        onClear: () {
          setState(() => _showOverdue = false);
          _load();
        },
      ));
    }

    if (_status != 'all') {
      chips.add(_filterChip(
        label: _status.replaceAll('-', ' '),
        onClear: () {
          setState(() => _status = 'all');
          _tabCtrl.index = 0;
          _load();
        },
      ));
    }

    if (_search.isNotEmpty) {
      chips.add(_filterChip(
        label: '“$_search”',
        onClear: () {
          setState(() => _search = '');
          _load();
        },
      ));
    }

    chips.add(
      OutlinedButton.icon(
        icon: const Icon(Icons.clear_all, size: 16),
        label: const Text('Reset'),
        onPressed: () {
          setState(() {
            _status = 'all';
            _tabCtrl.index = 0;
            _search = '';
            _propertyFilter = null;
            _assigneeFilter = null;
            _dateFrom = null;
            _dateTo = null;
            _showOverdue = false;
          });
          _load();
        },
      ),
    );

    return Padding(
      padding: const EdgeInsets.fromLTRB(12, 0, 12, 8),
      child: Wrap(spacing: 8, runSpacing: 8, children: chips),
    );
  }

  Widget _filterChip({required String label, required VoidCallback onClear}) {
    return Chip(
      label: Text(
        label,
        overflow: TextOverflow.ellipsis,
        style: const TextStyle(fontSize: 13.5, fontWeight: FontWeight.w600),
      ),
      deleteIcon: const Icon(Icons.close, size: 16),
      onDeleted: onClear,
    );
  }

  String _propertyName(int id) {
    try {
      return _properties.firstWhere((p) => p.id == id).name;
    } catch (_) {
      return 'Property #$id';
    }
  }

  String _assigneeName(int id) {
    try {
      return _assignees.firstWhere((u) => u.id == id).username;
    } catch (_) {
      return 'User #$id';
    }
  }

  // simple status color
  Color _statusColor(String status) {
    switch (status) {
      case 'pending':
        return Colors.orange.shade100;
      case 'in-progress':
        return Colors.blue.shade100;
      case 'completed':
        return Colors.green.shade100;
      case 'canceled':
        return Colors.red.shade100;
      default:
        return Colors.grey.shade200;
    }
  }
}

// ─────────────────────────────────────────────────────────────
//  A more spacious, overflow-safe task row
// ─────────────────────────────────────────────────────────────
class _TaskRow extends StatelessWidget {
  const _TaskRow({
    required this.task,
    required this.dateFmt,
    required this.dueBg,
    required this.dueFg,
    required this.dueLabel,
    required this.statusBg,
    required this.onTap,
  });

  final Task task;
  final DateFormat dateFmt;
  final Color Function(DateTime) dueBg;
  final Color Function(DateTime) dueFg;
  final String Function(DateTime) dueLabel;
  final Color statusBg;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      margin: const EdgeInsets.symmetric(vertical: 6),
      elevation: 1,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // main
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // title + muted
                    Row(
                      children: [
                        Expanded(
                          child: Text(
                            task.title,
                            maxLines: 2,
                            overflow: TextOverflow.ellipsis,
                            style: const TextStyle(
                              fontWeight: FontWeight.w800,
                              fontSize: 17,
                            ),
                          ),
                        ),
                        if (task.isMuted)
                          const Padding(
                            padding: EdgeInsets.only(left: 6),
                            child: Icon(Icons.notifications_off, size: 16, color: Colors.grey),
                          ),
                      ],
                    ),
                    const SizedBox(height: 6),

                    // Property • Created
                    Text(
                      "${task.propertyName} • ${dateFmt.format(task.createdAt)}",
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: theme.textTheme.bodySmall?.copyWith(fontSize: 13.5),
                    ),
                    const SizedBox(height: 8),

                    // creator → assignee + due
                    LayoutBuilder(
                      builder: (context, constraints) {
                        return Wrap(
                          spacing: 8,
                          runSpacing: 6,
                          crossAxisAlignment: WrapCrossAlignment.center,
                          children: [
                            const Icon(Icons.person_outline, size: 16, color: Colors.grey),
                            Text(
                              (task.createdBy ?? 'unknown'),
                              style: const TextStyle(fontSize: 13, color: Colors.grey),
                            ),
                            const Icon(Icons.arrow_forward, size: 16, color: Colors.grey),

                            ConstrainedBox(
                              constraints: BoxConstraints(maxWidth: constraints.maxWidth * 0.6),
                              child: Text(
                                (task.assignedToUsername ?? 'Not assigned'),
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                                style: const TextStyle(fontSize: 13, color: Colors.grey),
                              ),
                            ),

                            if (task.dueAt != null)
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                                decoration: BoxDecoration(
                                  color: dueBg(task.dueAt!),
                                  borderRadius: BorderRadius.circular(999),
                                ),
                                child: Row(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                    Icon(Icons.event, size: 16, color: dueFg(task.dueAt!)),
                                    const SizedBox(width: 6),
                                    Text(
                                      dueLabel(task.dueAt!),
                                      style: TextStyle(fontSize: 13, color: dueFg(task.dueAt!)),
                                    ),
                                  ],
                                ),
                              ),
                          ],
                        );
                      },
                    ),
                  ],
                ),
              ),

              const SizedBox(width: 10),

              // trailing status chip
              Chip(
                label: Text(
                  task.status.replaceAll('-', ' '),
                  style: const TextStyle(fontSize: 13),
                ),
                backgroundColor: statusBg,
                side: const BorderSide(color: Colors.black12),
                materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 0),
              ),
            ],
          ),
        ),
      ),
    );
  }
}