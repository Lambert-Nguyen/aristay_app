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
  String? _nextUrl;
  bool _isLoading = false;
  bool _isLoadingMore = false;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _fetchTasks(); // load first page
  }

  Future<void> _fetchTasks() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
      _tasks.clear();
      _nextUrl = null;
    });
    try {
      final result = await apiService.fetchCleaningTasks();
      setState(() {
        _tasks = result['results'] ?? [];
        _nextUrl = result['next'];
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

  Future<void> _loadMoreTasks() async {
    if (_nextUrl == null) return; // no more pages
    setState(() {
      _isLoadingMore = true;
    });
    try {
      final result = await apiService.fetchCleaningTasks(url: _nextUrl);
      setState(() {
        _tasks.addAll(result['results'] ?? []);
        _nextUrl = result['next'];
      });
    } catch (error) {
      // Optionally handle error
    } finally {
      setState(() {
        _isLoadingMore = false;
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
                  child: ListView.builder(
                    itemCount: _tasks.length + 1, // +1 for load more button
                    itemBuilder: (context, index) {
                      if (index < _tasks.length) {
                        final task = _tasks[index];
                        return ListTile(
                          title: Text(task['property_name'] ?? 'Unnamed'),
                          subtitle: Text('Status: ${task['status']}'),
                          onTap: () {
                            Navigator.pushNamed(context, '/task-detail', arguments: task);
                          },
                        );
                      } else {
                        // The last item is the "Load More" button
                        if (_nextUrl == null) {
                          return const SizedBox.shrink(); // no more pages
                        } else {
                          return Center(
                            child: _isLoadingMore
                                ? const Padding(
                                    padding: EdgeInsets.all(16.0),
                                    child: CircularProgressIndicator(),
                                  )
                                : TextButton(
                                    onPressed: _loadMoreTasks,
                                    child: const Text('Load More'),
                                  ),
                          );
                        }
                      }
                    },
                  ),
                ),
    );
  }
}