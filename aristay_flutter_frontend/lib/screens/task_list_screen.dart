import 'package:flutter/material.dart';
import '../models/task.dart';
import '../services/api_service.dart';

class TaskListScreen extends StatefulWidget {
  const TaskListScreen({Key? key}) : super(key: key);
  @override
  State<TaskListScreen> createState() => _TaskListScreenState();
}

class _TaskListScreenState extends State<TaskListScreen> {
  final ApiService _api = ApiService();
  List<Task> _tasks = [];
  String? _nextUrl;
  bool _isLoading = false, _isLoadingMore = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() { _isLoading = true; _error = null; });
    try {
      final res = await _api.fetchTasks();
      setState(() {
        _tasks = res['results'] as List<Task>;
        _nextUrl = res['next'] as String?;
      });
    } catch (e) {
      _error = 'Failed to load tasks: $e';
    } finally {
      setState(() { _isLoading = false; });
    }
  }

  Future<void> _loadMore() async {
    if (_nextUrl == null) return;
    setState(() { _isLoadingMore = true; });
    final res = await _api.fetchTasks(url: _nextUrl);
    setState(() {
      _tasks.addAll(res['results'] as List<Task>);
      _nextUrl = res['next'] as String?;
      _isLoadingMore = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) return const Scaffold(body: Center(child: CircularProgressIndicator()));
    if (_error != null) return Scaffold(body: Center(child: Text(_error!)));

    return Scaffold(
      appBar: AppBar(title: const Text('Cleaning Tasks')),
      body: RefreshIndicator(
        onRefresh: _load,
        child: ListView.builder(
          itemCount: _tasks.length + (_nextUrl != null ? 1 : 0),
          itemBuilder: (ctx, i) {
            if (i == _tasks.length) {
              return Center(
                child: _isLoadingMore
                  ? const Padding(
                      padding: EdgeInsets.all(16), 
                      child: CircularProgressIndicator(),
                    )
                  : TextButton(
                      child: const Text('Load More'),
                      onPressed: _loadMore,
                    ),
              );
            }
            final task = _tasks[i];
            return ListTile(
              title: Text(task.propertyName),
              subtitle: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Status: ${task.status}'),
                  Text('Created by: ${task.createdBy ?? "unknown"}'),
                ],
              ),
              isThreeLine: true,
              onTap: () => Navigator.pushNamed(
                context,
                '/task-detail',
                arguments: task,               // <<— pass the Task itself
              ),
            );
          },
        ),
      ),
    );
  }
}