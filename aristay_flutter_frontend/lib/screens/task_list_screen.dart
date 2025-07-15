import 'package:flutter/material.dart';
import '../widgets/task_filter_bar.dart';
import '../models/property.dart';
import '../models/user.dart';
import '../models/task.dart';
import '../services/api_service.dart';
import 'package:intl/intl.dart';

class TaskListScreen extends StatefulWidget {
  const TaskListScreen({Key? key}) : super(key: key);
  @override
  State<TaskListScreen> createState() => _TaskListScreenState();
}

class _TaskListScreenState extends State<TaskListScreen> {
  final _dateFmt = DateFormat.yMMMd(); // e.g. “Jul 15, 2025”
  final _api = ApiService();

  List<Task> _tasks = [];
  String? _nextUrl;
  bool _isLoading = false, _isLoadingMore = false;
  String? _error;

  String _search = '';
  String _status = 'all'; // start with “All”

  List<Property> _properties = [];
  List<User>     _assignees  = [];
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

  // fetchUsers now returns { 'results': List<User>, 'next': String? }
  final userResp = await _api.fetchUsers();
  final users    = userResp['results'] as List<User>;

  setState(() {
    _properties = props;
    _assignees  = users;
  });
}

  Future<void> _load({bool append = false}) async {
    setState(() => append ? _isLoadingMore = true : _isLoading = true);

    try {
      final statusParam = _status == 'all' ? null : _status;
      final res = await _api.fetchTasks(
        search:     _search,
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
        _error = null; // clear any previous error
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

  @override
  Widget build(BuildContext ctx) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Tasks'),
        bottom: PreferredSize(
        preferredSize: const Size.fromHeight(80),
        child: TaskFilterBar(
          properties:       _properties,
          assignees:        _assignees,
          selectedSearch:   _search,
          selectedStatus:   _status,
          selectedProperty: _propertyFilter,
          selectedAssignee:_assigneeFilter,
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
            setState(() {
              if (search    != null) _search          = search;
              if (status    != null) _status          = status;
              _propertyFilter   = property;
              _assigneeFilter   = assignedTo;
              _dateFrom         = dateFrom;
              _dateTo           = dateTo;
            });
            _load(); // re-fetch with all filters
          },
        ),
      ),
      ),
      body: RefreshIndicator(
        onRefresh: () => _load(),
        child: _isLoading
            ? const Center(child: CircularProgressIndicator())
            : _error != null
                // ─── Error State ───────────────────────────────────
                ? Center(
                    child: Padding(
                      padding: const EdgeInsets.all(20),
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(Icons.error_outline,
                              size: 48, color: Colors.redAccent),
                          const SizedBox(height: 12),
                          Text(
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
                  )
                // ─── Empty State ───────────────────────────────────
                : _tasks.isEmpty
                    ? Center(
                        child: Column(
                          mainAxisSize: MainAxisSize.min,
                          children: const [
                            Icon(Icons.inbox,
                                size: 48, color: Colors.grey),
                            SizedBox(height: 8),
                            Text(
                              'No tasks found.',
                              style: TextStyle(
                                  fontSize: 16, color: Colors.grey),
                            ),
                          ],
                        ),
                      )
                // ─── Data List ─────────────────────────────────────
                    : ListView.separated(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 12, vertical: 8),
                        itemCount:
                            _tasks.length + (_nextUrl != null ? 1 : 0),
                        separatorBuilder: (_, __) =>
                            const SizedBox(height: 12),
                        itemBuilder: (ctx, i) {
                          if (i == _tasks.length) {
                            return Center(
                              child: _isLoadingMore
                                  ? const CircularProgressIndicator()
                                  : ElevatedButton(
                                      onPressed: () =>
                                          _load(append: true),
                                      child: const Text('Load More'),
                                    ),
                            );
                          }
                          final t = _tasks[i];
                          return Card(
                            margin:
                                const EdgeInsets.symmetric(vertical: 6),
                            elevation: 1,
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(10),
                            ),
                            child: ExpansionTile(
                              tilePadding:
                                  const EdgeInsets.symmetric(
                                      horizontal: 16, vertical: 12),
                              title: Text(
                                t.title,
                                style: const TextStyle(
                                  fontSize: 18,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                              trailing: Chip(
                                label: Text(
                                  t.status.replaceAll('-', ' '),
                                  style: const TextStyle(
                                      color: Colors.black87,
                                      fontSize: 12),
                                ),
                                backgroundColor:
                                    _statusColor(t.status),
                              ),
                              children: [
                                Padding(
                                  padding:
                                      const EdgeInsets.symmetric(
                                          horizontal: 16, vertical: 8),
                                  child: Column(
                                    crossAxisAlignment:
                                        CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        "🏠 ${t.propertyName}  ·  ⏰ ${_dateFmt.format(t.createdAt)}",
                                        style:
                                            const TextStyle(fontSize: 14),
                                      ),
                                      const SizedBox(height: 4),
                                      Text(
                                        "👤 By: ${t.createdBy ?? '—'}  ·  🧑‍🤝‍🧑 Assigned: ${t.assignedToUsername ?? 'Unassigned'}",
                                        style:
                                            const TextStyle(fontSize: 14),
                                      ),
                                      const SizedBox(height: 8),
                                      Align(
                                        alignment: Alignment.centerRight,
                                        child: TextButton(
                                          onPressed: () {
                                            Navigator.pushNamed(
                                              context,
                                              '/task-detail',
                                              arguments: t,
                                            );
                                          },
                                          child: const Text(
                                            'View Details',
                                            style: TextStyle(
                                                fontSize: 14),
                                          ),
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                              ],
                            ),
                          );
                        },
                      ),
      ),
    );
  }
}