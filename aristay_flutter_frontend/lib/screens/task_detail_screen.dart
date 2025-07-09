// lib/screens/task_detail_screen.dart

import 'package:flutter/material.dart';
import '../models/task.dart';
import '../services/api_service.dart';

class TaskDetailScreen extends StatefulWidget {
  /// We accept the Task you passed in from the list,
  /// but immediately overwrite it with the fresh copy from the API.
  final Task initialTask;
  const TaskDetailScreen({Key? key, required this.initialTask}) : super(key: key);

  @override
  State<TaskDetailScreen> createState() => _TaskDetailScreenState();
}

class _TaskDetailScreenState extends State<TaskDetailScreen> {
  late Task _task;
  bool _loading = false;

  @override
  void initState() {
    super.initState();
    // Start with whatever you got from the list...
    _task = widget.initialTask;
    // ...then immediately fetch the latest from the backend.
    _refresh();
  }

  Future<void> _refresh() async {
    setState(() => _loading = true);
    try {
      final updated = await ApiService().fetchTask(_task.id);
      setState(() {
        _task = updated;
      });
    } catch (e) {
      debugPrint('Failed to refresh task: $e');
      // you could also show a SnackBar here if you like
    } finally {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Task Details'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _refresh,
          ),
          IconButton(
            icon: const Icon(Icons.edit),
            onPressed: () async {
              final result = await Navigator.pushNamed(
                context,
                '/edit-task',
                arguments: _task,
              );
              if (result == true) {
                await _refresh();
              }
            },
          ),
          IconButton(
            icon: const Icon(Icons.delete),
            onPressed: () async {
              final ok = await ApiService().deleteTask(_task.id);
              if (ok) {
                Navigator.popUntil(context, ModalRoute.withName('/tasks'));
              } else {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Delete failed')),
                );
              }
            },
          ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : Padding(
              padding: const EdgeInsets.all(16),
              child: ListView(
                children: [
                  Text('Task Type: ${_task.taskType}', style: const TextStyle(fontSize: 18)),
                  const SizedBox(height: 8),
                  Text('Title: ${_task.title}', style: const TextStyle(fontSize: 18)),
                  const SizedBox(height: 8),
                  Text('Description: ${_task.description}', style: const TextStyle(fontSize: 16)),
                  const Divider(height: 32),
                  Text('Property: ${_task.propertyName}', style: const TextStyle(fontSize: 16)),
                  const SizedBox(height: 8),
                  Text('Status: ${_task.status}', style: const TextStyle(fontSize: 16)),
                  const SizedBox(height: 8),
                  Text('Created by: ${_task.createdBy ?? "unknown"}',
                      style: const TextStyle(fontSize: 16)),
                  const SizedBox(height: 8),
                  Text('Assigned to: ${_task.assignedToUsername ?? "Not assigned"}',
                      style: const TextStyle(fontSize: 16)),
                  const SizedBox(height: 8),
                  Text('Modified by: ${_task.modifiedBy ?? _task.createdBy ?? "n/a"}',
                      style: const TextStyle(fontSize: 16)),
                  const Divider(height: 32),
                  const Text('History:',
                      style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 8),
                  if (_task.history.isEmpty)
                    const Text('No history available', style: TextStyle(fontSize: 16))
                  else
                    ..._task.history.map((entry) => Padding(
                          padding: const EdgeInsets.symmetric(vertical: 4),
                          child: Text('• $entry', style: const TextStyle(fontSize: 16)),
                        )),
                ],
              ),
            ),
    );
  }
}