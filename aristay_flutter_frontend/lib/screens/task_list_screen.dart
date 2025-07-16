import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../widgets/task_filter_bar.dart';
import '../models/property.dart';
import '../models/user.dart';
import '../models/task.dart';
import '../services/api_service.dart';

class TaskListScreen extends StatefulWidget {
  const TaskListScreen({Key? key}) : super(key: key);

  @override
  State<TaskListScreen> createState() => _TaskListScreenState();
}

class _TaskListScreenState extends State<TaskListScreen> {
  final _dateFmt = DateFormat.yMMMd(); // e.g. “Jul 15, 2025”
  final _api = ApiService();

  // ─── Data + pagination state ─────────────────────────────────────────
  List<Task> _tasks = [];
  String? _nextUrl;
  bool _isLoading = false, _isLoadingMore = false;
  String? _error;

  // ─── Filter + status state ────────────────────────────────────────────
  String _search = '';
  String _status = 'all';
  final _statusOptions = ['all', 'pending', 'in-progress', 'completed', 'canceled'];

  List<Property> _properties = [];
  List<User> _assignees = [];
  int? _propertyFilter;
  int? _assigneeFilter;
  DateTime? _dateFrom;
  DateTime? _dateTo;

  @override
  void initState() {
    super.initState();
    _loadFilters();
    _load();
  }

  Future<void> _loadFilters() async {
    final props = await _api.fetchProperties();
    final userResp = await _api.fetchUsers();          // { 'results': List<User>, 'next': ... }
    final users = userResp['results'] as List<User>;

    setState(() {
      _properties = props;
      _assignees = users;
    });
  }

  Future<void> _load({bool append = false}) async {
    setState(() => append ? _isLoadingMore = true : _isLoading = true);
    try {
      final statusParam = _status == 'all' ? null : _status;
      final res = await _api.fetchTasks(
        search:     _search.isEmpty ? null : _search,
        status:     statusParam,
        property:   _propertyFilter,
        assignedTo: _assigneeFilter,
        dateFrom:   _dateFrom,
        dateTo:     _dateTo,
      );

      setState(() {
        if (append) {
          _tasks.addAll(res['results'] as List<Task>);
        } else {
          _tasks = res['results'] as List<Task>;
        }
        _nextUrl = res['next'] as String?;
        _error = null;
      });
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      setState(() {
        _isLoading = false;
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

  void _openFilterSheet() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (_) => Padding(
        padding: EdgeInsets.only(bottom: MediaQuery.of(context).viewInsets.bottom),
        child: TaskFilterBar(
          properties:       _properties,
          assignees:        _assignees,
          selectedSearch:   _search,
          selectedStatus:   _status,
          selectedProperty: _propertyFilter,
          selectedAssignee: _assigneeFilter,
          dateFrom:         _dateFrom,
          dateTo:           _dateTo,
          onFilter: ({
            String? search,
            String? status,
            int? property,
            int? assignedTo,
            DateTime? dateFrom,
            DateTime? dateTo,
          }) {
            Navigator.pop(context);
            setState(() {
              _search         = search    ?? '';
              _status         = status    ?? 'all';
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
          IconButton(
            icon: const Icon(Icons.filter_alt_outlined),
            tooltip: 'More filters',
            onPressed: _openFilterSheet,
          ),
        ],
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(48),
          child: Padding(
            padding: const EdgeInsets.symmetric(vertical: 8),
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
                final label = s == 'all' ? 'All' : s.replaceAll('-', ' ');
                return Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 12),
                  child: Text(label),
                );
              }).toList(),
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
          Navigator.pushNamed(ctx, '/task-add').then((_) => _load());
        },
      ),
    );
  }

  Widget _buildError() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.error_outline, size: 48, color: Colors.redAccent),
            const SizedBox(height: 12),
            const Text(
              'Oops! Failed to load tasks.',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
                color: Colors.redAccent,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              _error!,
              textAlign: TextAlign.center,
              style: const TextStyle(fontSize: 14),
            ),
            const SizedBox(height: 12),
            ElevatedButton(
              onPressed: () {
                setState(() => _error = null);
                _load();
              },
              child: const Text('Retry'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildEmpty() {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: const [
          Icon(Icons.inbox, size: 48, color: Colors.grey),
          SizedBox(height: 8),
          Text(
            'No tasks found.',
            style: TextStyle(fontSize: 16, color: Colors.grey),
          ),
        ],
      ),
    );
  }

  Widget _buildList() {
    return ListView.separated(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      itemCount: _tasks.length + (_nextUrl != null ? 1 : 0),
      separatorBuilder: (_, __) => const SizedBox(height: 12),
      itemBuilder: (ctx, i) {
        if (i == _tasks.length) {
          return Center(
            child: _isLoadingMore
                ? const CircularProgressIndicator()
                : ElevatedButton(
                    child: const Text('Load More'),
                    onPressed: () => _load(append: true),
                  ),
          );
        }
        final t = _tasks[i];
        return Card(
          margin: const EdgeInsets.symmetric(vertical: 6),
          elevation: 1,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(10),
          ),
          child: ExpansionTile(
            tilePadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            title: Text(
              t.title,
              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            trailing: Chip(
              label: Text(
                t.status.replaceAll('-', ' '),
                style: const TextStyle(color: Colors.black87, fontSize: 12),
              ),
              backgroundColor: _statusColor(t.status),
            ),
            children: [
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      "🏠 ${t.propertyName}  ·  ⏰ ${_dateFmt.format(t.createdAt)}",
                      style: const TextStyle(fontSize: 14),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      "👤 By: ${t.createdBy ?? '—'}  ·  🧑‍🤝‍🧑 Assigned: ${t.assignedToUsername ?? 'Unassigned'}",
                      style: const TextStyle(fontSize: 14),
                    ),
                    const SizedBox(height: 8),
                    Align(
                      alignment: Alignment.centerRight,
                      child: TextButton(
                        child: const Text('View Details', style: TextStyle(fontSize: 14)),
                        onPressed: () {
                          Navigator.pushNamed(ctx, '/task-detail', arguments: t);
                        },
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}