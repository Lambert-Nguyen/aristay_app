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

class _TaskListScreenState extends State<TaskListScreen> {
  final _dateFmt      = DateFormat.yMMMd();
  final _api          = ApiService();
  final _statusOptions = ['pending', 'in-progress', 'completed', 'canceled'];

  // ─── state + infinite‐scroll controller ───────────────
  List<Task>   _tasks     = [];
  String?      _nextUrl;
  bool         _isLoading = false, _isLoadingMore = false;
  String?      _error;
  
  // total on the server
  int      _totalCount   = 0;
  // per‐status counts
  Map<String,int> _statusCounts = {};
  // last time we fetched fresh data
  DateTime? _lastUpdated;

  String       _search    = '';
  String       _status    = 'all';

  List<Property> _properties = [];
  List<User>     _assignees  = [];
  int?           _propertyFilter;
  int?           _assigneeFilter;
  DateTime?      _dateFrom;
  DateTime?      _dateTo;

  bool _showOverdue = false;
  bool _initializedFromArgs = false;


  // controller to drive infinite scroll
  late final ScrollController _scrollCtrl;

  @override
  void initState() {
    super.initState();
    // hook up the scroll controller
    _scrollCtrl = ScrollController()
      ..addListener(() {
        final pos = _scrollCtrl.position;
        if (!_isLoadingMore && _nextUrl != null
            && pos.pixels >= pos.maxScrollExtent * 0.8) {
          _load(append: true);
        }
      });
    _loadFilters();
    // first load tasks, then counts
    _load().then((_) => _loadCounts());
  }

  @override
  void dispose() {
    _scrollCtrl.dispose();
    super.dispose();
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (_initializedFromArgs) return;

    final args = ModalRoute.of(context)?.settings.arguments;
    if (args is Map) {
      final String? status = args['status'] as String?;
      final bool overdue   = (args['overdue'] as bool?) ?? false;
      final int? assignedTo = args['assignedTo'] as int?;

      if (status != null) _status = status == 'all' ? 'all' : status;
      _showOverdue    = overdue;
      _assigneeFilter = assignedTo;

      _search = '';
      _propertyFilter = null;
      _dateFrom = null; _dateTo = null;

      _load().then((_) => _loadCounts());
    }
    _initializedFromArgs = true;
  }

  Future<void> _loadFilters() async {
    final props    = await _api.fetchProperties();
    final usersRes = await _api.fetchUsers();
    setState(() {
      _properties = props;
      _assignees  = usersRes['results'] as List<User>;
    });
  }

  Future<void> _loadCounts() async {
    try {
      final data = await _api.fetchTaskCounts();
      setState(() {
        _totalCount   = data['total'] as int;
        _statusCounts = Map<String,int>.from(data['by_status']);
      });
    } catch (_) {
      // ignore errors for now
    }
  }

  Future<void> _load({bool append = false}) async {
    setState(() => append ? _isLoadingMore = true : _isLoading = true);
    try {
      // decide whether to page or to fetch fresh
      final Map<String, dynamic> res;
      if (append && _nextUrl != null) {
        // load the next page
        res = await _api.fetchTasks(url: _nextUrl);
      } else {
        // fresh load (first page, or filter changed)
        res = await _api.fetchTasks(
          search:     _search.isEmpty ? null : _search,
          status:     _status == 'all' ? null : _status,
          property:   _propertyFilter,
          assignedTo: _assigneeFilter,
          dateFrom:   _dateFrom,
          dateTo:     _dateTo,
          overdue:    _showOverdue,
        );
        // if not appending, clear out the old list
        _tasks = [];
      }

      setState(() {
        // append or replace
        final page = res['results'] as List<Task>;
        if (append) {
          _tasks.addAll(page);
        } else {
          _tasks = page;
          // record the fetch timestamp
          _lastUpdated = DateTime.now();

        }
        _nextUrl = res['next'] as String?;
        _error   = null;
      });
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      if (!append) _loadCounts();
      setState(() {
        _isLoading     = false;
        _isLoadingMore = false;
      });
    }
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

  Color _statusColor(String status) {
    switch (status) {
      case 'pending':     return Colors.orange.shade100;
      case 'in-progress': return Colors.blue.shade100;
      case 'completed':   return Colors.green.shade100;
      case 'canceled':    return Colors.red.shade100;
      default:            return Colors.grey.shade200;
    }
  }

  void _openAdvancedFilters() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (_) => Padding(
        padding: EdgeInsets.only(
          bottom: MediaQuery.of(context).viewInsets.bottom
        ),
        child: TaskAdvancedFilterSheet(
          properties:       _properties,
          assignees:        _assignees,
          selectedProperty: _propertyFilter,
          selectedAssignee: _assigneeFilter,
          dateFrom:         _dateFrom,
          dateTo:           _dateTo,
          overdue:          _showOverdue,
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
              _dateFrom       = dateFrom;
              _dateTo         = dateTo;
              _showOverdue    = overdue ?? false;
            });
            _load();
          },
        ),
      ),
    );
  }

  String _updatedAgo() {
    if (_lastUpdated == null) return '';
    final d = DateTime.now().difference(_lastUpdated!);
    if (d.inSeconds < 60) return 'Updated just now';
    if (d.inMinutes < 60) return 'Updated ${d.inMinutes}m ago';
    if (d.inHours   < 24) return 'Updated ${d.inHours}h ago';
    return 'Updated ${DateFormat.yMMMd().add_jm().format(_lastUpdated!.toLocal())}';
  }

  @override
  Widget build(BuildContext ctx) {
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
          // show “All(##)” and reset the status filter
          TextButton(
            onPressed: () {
              setState(() {
                _status         = 'all';
                _search         = '';
                _propertyFilter = null;
                _assigneeFilter = null;
                _dateFrom       = null;
                _dateTo         = null;
                _showOverdue    = false;
              });
              _load().then((_) => _loadCounts());
            },
            style: TextButton.styleFrom(
              // use the same color AppBar uses for its icons/text:
              foregroundColor: Theme.of(context).iconTheme.color,
              // shrink the padding to match IconButtons more closely:
              padding: const EdgeInsets.symmetric(horizontal: 8.0),
              minimumSize: const Size(0, 0),
              tapTargetSize: MaterialTapTargetSize.shrinkWrap,
            ),
            child: Text('All($_totalCount)'),
          ),
          if (_search.isNotEmpty)
            IconButton(
              icon: const Icon(Icons.clear),
              tooltip: 'Clear search',
              onPressed: () {
                setState(() {
                  _search = '';
                });
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
              setState(() {
                // if the user cancelled (result==null) we clear the filter
                _search = result ?? '';
              });
              _load(); 
            },
          ),
          IconButton(
            icon: const Icon(Icons.filter_alt_outlined),
            tooltip: 'More filters',
            onPressed: _openAdvancedFilters,
          ),
        ],
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(56),
          child: SizedBox(
            height: 48,
            child: SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              child: ToggleButtons(
                isSelected: _statusOptions.map((s) => s == _status).toList(),
                onPressed: (idx) {
                  setState(() => _status = _statusOptions[idx]);
                  _load();
                },
                borderRadius: BorderRadius.circular(8),
                selectedColor: Colors.white,
                fillColor: Theme.of(context).primaryColor,
                children: _statusOptions.map((s) {
                  final count = _statusCounts[s] ?? 0;
                  final label = '${s.replaceAll('-', ' ')} ($count)';
                  return Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 12),
                    child: Text(label),
                  );
                }).toList(), 
              ),             
            ),               
          ),                 
        ),                   
      ),

      body: RefreshIndicator(
        onRefresh: () => _load(),
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
        child: const Icon(Icons.add),
        onPressed: () {
        Navigator.pushNamed(ctx, '/create-task').then((_) => _load());
        },
      ),
    );
  }

  Widget _buildError() => Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.error_outline, size: 48, color: Colors.redAccent),
            const SizedBox(height: 12),
            Text(
              'Oops! Failed to load tasks.',
              style: Theme.of(context)
                    .textTheme
                    .titleLarge    // ← replacement for headline6
                    ?.copyWith(
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
      onPrimaryAction: () => Navigator.pushNamed(context, '/create-task').then((_) => _load()),
      secondaryActionLabel: _hasActiveFilters ? 'Reset filters' : null,
      onSecondaryAction: _hasActiveFilters
          ? () {
              setState(() {
                _status         = 'all';
                _search         = '';
                _propertyFilter = null;
                _assigneeFilter = null;
                _dateFrom       = null;
                _dateTo         = null;
                _showOverdue    = false;
              });
              _load();
            }
          : null,
    );
  }

  Widget _buildList() {
    // we're reserving index 0 for the "Updated at…" header, and
    // one slot at the end for the loading spinner if _nextUrl != null
    final showFooter = _nextUrl != null;
    final itemCount  = 1 + _tasks.length + (showFooter ? 1 : 0);

    return ListView.separated(
      controller: _scrollCtrl,
      padding:    const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      itemCount:  itemCount,
      separatorBuilder: (_, __) => const SizedBox(height: 12),
      itemBuilder: (ctx, i) {
        // ── HEADER ─────────────────────────────────────────────────────
        if (i == 0) {
          final time = _lastUpdated == null ? '' : DateFormat.jm().format(_lastUpdated!);
          return Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              if (time.isNotEmpty)
                Padding(
                  padding: EdgeInsets.only(
                    left: 4,
                    bottom: (_hasActiveFilters || _search.isNotEmpty) ? 4 : 8,
                  ),
                  child: Text('Updated at $time',
                      style: const TextStyle(fontSize: 14, color: Colors.grey)),
                ),
              if (_hasActiveFilters || _search.isNotEmpty)
                _activeFiltersChips(), // ← now visible above the list
            ],
          );
        }

        // calculate the real task index
        final taskIdx = i - 1;

        // ── FOOTER SPINNER ─────────────────────────────────────────────
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

        // ── TASK ROW ───────────────────────────────────────────────────
        final t = _tasks[taskIdx];
        return Card(
          margin: const EdgeInsets.symmetric(vertical: 6),
          elevation: 1,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(10),
          ),
          child: ListTile(
            contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),

            onTap: () async {
              final result = await Navigator.pushNamed(ctx, '/task-detail', arguments: t);
              if (!mounted) return;
              if (result is Task) {
                final idx = _tasks.indexWhere((x) => x.id == result.id);
                if (idx != -1) setState(() => _tasks[idx] = result);
              }
            },

            title: Row(
              children: [
                Expanded(
                  child: Text(
                    t.title,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(fontWeight: FontWeight.bold),
                  ),
                ),
                if (t.isMuted)
                  const Icon(Icons.notifications_off, size: 16, color: Colors.grey),
              ],
            ),

            subtitle: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // line 1: property • created (ellipsize)
                Text(
                  "${t.propertyName} • ${_dateFmt.format(t.createdAt)}",
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 4),

                // line 2: creator → assignee + due pill (wrap on small screens)
                LayoutBuilder(
                  builder: (context, constraints) {
                    return Wrap(
                      spacing: 6,
                      runSpacing: 6,
                      crossAxisAlignment: WrapCrossAlignment.center,
                      children: [
                        const Icon(Icons.person_outline, size: 14, color: Colors.grey),
                        Text(
                          (t.createdBy ?? 'unknown'),
                          style: const TextStyle(fontSize: 12, color: Colors.grey),
                        ),
                        const Icon(Icons.arrow_forward, size: 14, color: Colors.grey),

                        // cap assignee width so the due pill can wrap
                        ConstrainedBox(
                          constraints: BoxConstraints(maxWidth: constraints.maxWidth * 0.6),
                          child: Text(
                            (t.assignedToUsername ?? 'Not assigned'),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: const TextStyle(fontSize: 12, color: Colors.grey),
                          ),
                        ),

                        if (t.dueAt != null)
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                            decoration: BoxDecoration(
                              color: _dueBg(t.dueAt!),
                              borderRadius: BorderRadius.circular(999),
                            ),
                            child: Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                Icon(Icons.event, size: 14, color: _dueFg(t.dueAt!)),
                                const SizedBox(width: 4),
                                Text(
                                  _dueLabel(t.dueAt!),
                                  style: TextStyle(fontSize: 12, color: _dueFg(t.dueAt!)),
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

            // status chip stays on the right
            trailing: Chip(
              label: Text(t.status.replaceAll('-', ' ')),
              backgroundColor: _statusColor(t.status),
              side: const BorderSide(color: Colors.black12),
            ),
          )
        );
      },
    );
  }
  bool get _hasActiveFilters =>
      _propertyFilter != null ||
      _assigneeFilter != null ||
      _dateFrom != null ||
      _dateTo != null ||
      _showOverdue;

  Widget _filterChip({required String label, required VoidCallback onClear}) {
    return Chip(
      label: Text(label, overflow: TextOverflow.ellipsis),
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

  Widget _activeFiltersChips() {
    final chips = <Widget>[];

    if (_propertyFilter != null) {
      chips.add(_filterChip(
        label: _propertyName(_propertyFilter!),
        onClear: () { setState(() => _propertyFilter = null); _load(); },
      ));
    }

    if (_assigneeFilter != null) {
      chips.add(_filterChip(
        label: _assigneeName(_assigneeFilter!),
        onClear: () { setState(() => _assigneeFilter = null); _load(); },
      ));
    }

    if (_dateFrom != null || _dateTo != null) {
      final from = _dateFrom != null ? DateFormat.yMMMd().format(_dateFrom!) : '…';
      final to   = _dateTo   != null ? DateFormat.yMMMd().format(_dateTo!)   : '…';
      chips.add(_filterChip(
        label: '$from → $to',
        onClear: () { setState(() { _dateFrom = null; _dateTo = null; }); _load(); },
      ));
    }

    if (_showOverdue) {
      chips.add(_filterChip(
        label: 'Overdue only',
        onClear: () { setState(() => _showOverdue = false); _load(); },
      ));
    }

    // trailing all-in reset (optional)
    chips.add(
      OutlinedButton.icon(
        icon: const Icon(Icons.clear_all, size: 16),
        label: const Text('Reset'),
        onPressed: () {
          setState(() {
            _status         = 'all';
            _search         = '';
            _propertyFilter = null;
            _assigneeFilter = null;
            _dateFrom       = null;
            _dateTo         = null;
            _showOverdue    = false;
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
}