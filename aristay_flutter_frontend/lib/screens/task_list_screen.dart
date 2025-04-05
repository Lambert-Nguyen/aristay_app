import 'package:flutter/material.dart';
import '../services/api_service.dart';

class TaskListScreen extends StatefulWidget {
  const TaskListScreen({Key? key}) : super(key: key);

  @override
  State<TaskListScreen> createState() => _TaskListScreenState();
}

class _TaskListScreenState extends State<TaskListScreen> {
  final ApiService apiService = ApiService();
  List<dynamic> _tasks = [];
  bool _isLoading = false;
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
    });
    try {
      final tasks = await apiService.fetchCleaningTasks();
      setState(() {
        _tasks = tasks ?? [];
      });
    } catch (error) {
      setState(() {
        _errorMessage = 'Failed to load tasks: $error';
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  Future<void> _refreshTasks() async {
    await _fetchTasks();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Cleaning Tasks'),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _errorMessage != null
              ? Center(child: Text(_errorMessage!))
              : RefreshIndicator(
                  onRefresh: _refreshTasks,
                  child: _tasks.isEmpty
                      ? const Center(child: Text('No tasks available'))
                      : ListView.builder(
                          itemCount: _tasks.length,
                          itemBuilder: (context, index) {
                            final task = _tasks[index];
                            return ListTile(
                              title: Text(task['property_name'] ?? 'Unnamed'),
                              subtitle: Text('Status: ${task['status']}'),
                            );
                          },
                        ),
                ),
    );
  }
}