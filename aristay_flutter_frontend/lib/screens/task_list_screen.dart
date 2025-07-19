import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../widgets/task_advanced_filter_sheet.dart';  // ← new
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
          onApply: ({
            int? property,
            int? assignedTo,
            DateTime? dateFrom,
            DateTime? dateTo,
          }) {
            setState(() {
              _propertyFilter = property;
              _assigneeFilter = assignedTo;
              _dateFrom       = dateFrom;
              _dateTo         = dateTo;
            });
            _load();
          },
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext ctx) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Tasks'),
        actions: [
          // show “All(##)” and reset the status filter
          TextButton(
            onPressed: () {
              if (_status != 'all') {
                setState(() => _status = 'all');
                _load().then((_) => _loadCounts());
              }
            },
            child: Text(
              'All($_totalCount)',
              style: const TextStyle(color: Colors.white),
            ),
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

  Widget _buildEmpty() => Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: const [
            Icon(Icons.inbox, size: 48, color: Colors.grey),
            SizedBox(height: 8),
            Text('No tasks found.', style: TextStyle(color: Colors.grey)),
          ],
        ),
      );

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
          final time = _lastUpdated == null
              ? ''
              : DateFormat.jm().format(_lastUpdated!);
          return Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: Text(
              time.isEmpty ? '' : 'Updated at $time',
              style: const TextStyle(fontSize: 14, color: Colors.grey),
            ),
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
            contentPadding:
                const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            title: Text(t.title,
                style: const TextStyle(fontWeight: FontWeight.bold)),
            subtitle: Text(
              "${t.propertyName} • ${_dateFmt.format(t.createdAt)}",
            ),
            trailing: Chip(
              label: Text(t.status.replaceAll('-', ' ')),
              backgroundColor: _statusColor(t.status),
            ),
            onTap: () =>
                Navigator.pushNamed(ctx, '/task-detail', arguments: t),
          ),
        );
      },
    );
  }
}