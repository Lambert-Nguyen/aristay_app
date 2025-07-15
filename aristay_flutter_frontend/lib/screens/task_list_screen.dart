import 'package:flutter/material.dart';
import '../models/task.dart';
import '../services/api_service.dart';

class TaskListScreen extends StatefulWidget {
  const TaskListScreen({Key? key}) : super(key: key);
  @override
  State<TaskListScreen> createState() => _TaskListScreenState();
}

class _TaskListScreenState extends State<TaskListScreen> {
  final _api = ApiService();
  List<Task> _tasks = [];
  String? _nextUrl;
  bool _isLoading = false, _isLoadingMore = false;
  String? _error;

  String _search = '';
  String _status = 'pending';

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load({bool append = false}) async {
    setState(() => append ? _isLoadingMore = true : _isLoading = true);
    try {
      final res = await _api.fetchTasks(search: _search, status: _status);
      setState(() {
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
                  items: ['pending', 'in-progress', 'completed', 'canceled']
                      .map((s) => DropdownMenuItem(value: s, child: Text(s)))
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
                      final t = _tasks[i];
                      return Card(
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(10),
                        ),
                        elevation: 2,
                        child: ListTile(
                          contentPadding: const EdgeInsets.symmetric(
                              horizontal: 16, vertical: 12),
                          title: Text(t.title,
                              style: const TextStyle(
                                  fontWeight: FontWeight.w600)),
                          subtitle: Text(
                              'Property: ${t.propertyName}  ·  Created: ${t.createdAt.toIso8601String().substring(0,10)}',
                            maxLines: 2,
                            overflow: TextOverflow.ellipsis,
                          ),
                          trailing: Chip(label: Text(t.status)),
                          onTap: () => Navigator.pushNamed(
                              ctx, '/task-detail',
                              arguments: t),
                        ),
                      );
                    },
                  ),
      ),
    );
  }
}