import 'package:flutter/material.dart';
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
  // start with "all" to fetch everything
  String _status = 'all';

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load({bool append = false}) async {
    setState(() => append ? _isLoadingMore = true : _isLoading = true);
    try {
        // only filter if _status isn't "all"
        final statusParam = _status == 'all' ? null : _status;
        final res = await _api.fetchTasks(search: _search, status: statusParam);      setState(() {
        if (append) {
          _tasks.addAll(res['results'] as List<Task>);
        } else {
          _tasks = res['results'] as List<Task>;
        }
        _nextUrl = res['next'] as String?;
      });
    } catch (e) {
      setState(() => _error = 'Load failed: $e');
    } finally {
      setState(() {
        _isLoading = false;
        _isLoadingMore = false;
      });
    }
  }
  // ──────────────────────────────────────
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
  // ──────────────────────────────────────

  @override
  Widget build(BuildContext ctx) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Tasks'),
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(56),
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            child: Row(
              children: [
                // 1) Search field
                Expanded(
                  child: TextField(
                    decoration: InputDecoration(
                      hintText: 'Search…',
                      prefixIcon: const Icon(Icons.search),
                      filled: true,
                      fillColor: Colors.white,
                      contentPadding: const EdgeInsets.symmetric(vertical: 0),
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(8),
                        borderSide: BorderSide.none,
                      ),
                    ),
                    onSubmitted: (q) {
                      _search = q.trim();
                      _load();
                    },
                  ),
                ),
                const SizedBox(width: 8),
                // 2) Status dropdown
                DropdownButton<String>(
                  value: _status,
                  underline: const SizedBox(),
                  onChanged: (v) {
                    setState(() => _status = v!);
                    _load();
                  },
                  items: ['all', 'pending', 'in-progress', 'completed', 'canceled']
                      .map((s) => DropdownMenuItem(
                        value: s,
                            child: Text(
                              s == 'all'
                                ? 'All'
                                : // optionally prettify hyphens:
                                  s.replaceAll('-', ' ').replaceFirstMapped(
                                    RegExp(r'^\w'),
                                    (m) => m.group(0)!.toUpperCase(),
                                  ),
                            ),
                          ))
                      .toList(),
                ),
              ],
            ),
          ),
        ),
      ),
      body: RefreshIndicator(
        onRefresh: () => _load(),
        child: _isLoading
            ? const Center(child: CircularProgressIndicator())
            : _error != null
                ? Center(child: Text(_error!))
                : ListView.separated(
                    padding: const EdgeInsets.all(12),
                    itemCount: _tasks.length + (_nextUrl != null ? 1 : 0),
                    separatorBuilder: (_, __) => const SizedBox(height: 12),
                    itemBuilder: (ctx, i) {
                      if (i == _tasks.length) {
                        // Load more button
                        return Center(
                          child: _isLoadingMore
                              ? const CircularProgressIndicator()
                              : ElevatedButton(
                                  onPressed: () => _load(append: true),
                                  child: const Text('Load More'),
                                ),
                        );
                      }
                      // inside your ListView.separated.itemBuilder:
                      final t = _tasks[i];
                      return Card(
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                        elevation: 2,
                        child: ExpansionTile(
                          tilePadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                          title: Text(
                            t.title,
                            style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                          ),
                          trailing: Chip(
                            label: Text(t.status),
                            backgroundColor: _statusColor(t.status),
                          ),
                          children: [
                            Padding(
                              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text("🏠 ${t.propertyName} · ⏰ ${_dateFmt.format(t.createdAt)}"),
                                  const SizedBox(height: 4),
                                  Text("👤 By: ${t.createdBy ?? '—'} · 🧑‍🤝‍🧑 Assigned: ${t.assignedToUsername ?? 'Unassigned'}"),
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
                                      child: const Text('View Details'),
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