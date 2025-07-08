import 'package:flutter/material.dart';
import '../models/task.dart';
import '../services/api_service.dart';
import 'task_detail_screen.dart';

class TaskListScreen extends StatefulWidget {
  const TaskListScreen({Key? key}) : super(key: key);

  @override
  State<TaskListScreen> createState() => _TaskListScreenState();
}

class _TaskListScreenState extends State<TaskListScreen> {
  final ApiService apiService = ApiService();
  List<Task> _tasks = [];
  String? _nextUrl;
  bool _isLoading = false;
  bool _isLoadingMore = false;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _fetchTasks();
  }

  Future<void> _fetchTasks() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
      _tasks.clear();
      _nextUrl = null;
    });
    try {
      final result = await apiService.fetchTasks();
      final raw = result['results'] as List<dynamic>;
      setState(() {
        _tasks = raw.map((e) => Task.fromJson(e as Map<String, dynamic>)).toList();
        _nextUrl = result['next'] as String?;
      });
    } catch (e) {
      setState(() { _errorMessage = 'Failed to load tasks: $e'; });
    } finally {
      setState(() { _isLoading = false; });
    }
  }

  Future<void> _loadMoreTasks() async {
    if (_nextUrl == null) return;
    setState(() { _isLoadingMore = true; });
    try {
      final result = await apiService.fetchTasks(url: _nextUrl);
      final raw = result['results'] as List<dynamic>;
      setState(() {
        _tasks.addAll(raw.map((e) => Task.fromJson(e as Map<String, dynamic>)));
        _nextUrl = result['next'] as String?;
      });
    } finally {
      setState(() { _isLoadingMore = false; });
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }
    if (_errorMessage != null) {
      return Scaffold(body: Center(child: Text(_errorMessage!)));
    }
    return Scaffold(
      appBar: AppBar(title: const Text('Cleaning Tasks')),
      body: RefreshIndicator(
        onRefresh: _fetchTasks,
        child: ListView.builder(
          itemCount: _tasks.length + (_nextUrl != null ? 1 : 0),
          itemBuilder: (context, index) {
            if (index < _tasks.length) {
              final task = _tasks[index];
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
                  arguments: task.toJson(),
                ),
              );
            }
            return Center(
              child: _isLoadingMore
                  ? const Padding(
                      padding: EdgeInsets.all(16),
                      child: CircularProgressIndicator(),
                    )
                  : TextButton(
                      onPressed: _loadMoreTasks,
                      child: const Text('Load More'),
                    ),
            );
          },
        ),
      ),
    );
  }
}