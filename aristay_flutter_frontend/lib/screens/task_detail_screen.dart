import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/task.dart';

class TaskDetailScreen extends StatefulWidget {
  final Task task;                  // <<— now accepts a Task
  const TaskDetailScreen({super.key, required this.task});

  @override
  State<TaskDetailScreen> createState() => _TaskDetailScreenState();
}

class _TaskDetailScreenState extends State<TaskDetailScreen> {
  String? _user;
  bool _canEdit = false;

  @override
  void initState() {
    super.initState();
    _initUser();
  }

  Future<void> _initUser() async {
    final prefs = await SharedPreferences.getInstance();
    final me = prefs.getString('username')?.trim().toLowerCase();
    setState(() {
      _user = me;
      _canEdit = (widget.task.createdBy?.toLowerCase() == me);
    });
  }

  @override
  Widget build(BuildContext c) {
    final t = widget.task;
    return Scaffold(
      appBar: AppBar(
        title: const Text('Task Details'),
        actions: [
          if (_canEdit)
            IconButton(
              icon: const Icon(Icons.edit),
              onPressed: () => Navigator.pushNamed(
                c, '/edit-task',
                arguments: t,
              ),
            )
        ],
      ),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: ListView(
          children: [
            Text('Task type: ${t.taskType}', style: const TextStyle(fontSize: 16)),
            const SizedBox(height: 8),
            Text('Title: ${t.title}', style: const TextStyle(fontSize: 16)),
            const SizedBox(height: 8),
            Text('Description: ${t.description}', style: const TextStyle(fontSize: 16)),
            const Divider(height: 32),
            Text('Property: ${t.propertyName}', style: const TextStyle(fontSize: 16)),
            const SizedBox(height: 8),
            Text('Status: ${t.status}', style: const TextStyle(fontSize: 16)),
            const SizedBox(height: 8),
            Text('Created by: ${t.createdBy ?? "unknown"}', style: const TextStyle(fontSize: 16)),
            const SizedBox(height: 8),
            Text('Assigned to: ${t.assignedTo ?? "unassigned"}', style: const TextStyle(fontSize: 16)),
            const SizedBox(height: 8),
            Text('Modified by: ${t.modifiedBy ?? "-"}', style: const TextStyle(fontSize: 16)),
            const Divider(height: 32),
            const Text('History:', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            if (t.history.isEmpty)
              const Text('No history available')
            else
              ...t.history.map((h) => Text('• $h')).toList(),
          ],
        ),
      ),
    );
  }
}