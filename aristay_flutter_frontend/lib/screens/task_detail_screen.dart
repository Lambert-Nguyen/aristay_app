import 'package:flutter/material.dart';
import '../models/task.dart';
import '../services/api_service.dart';

class TaskDetailScreen extends StatelessWidget {
  final Task task;
  const TaskDetailScreen({Key? key, required this.task}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    // You may also want to pull the current user from SharedPreferences
    // to conditionally show edit/delete buttons only for owner/assignee/admin.
    return Scaffold(
      appBar: AppBar(
        title: const Text('Task Details'),
        actions: [
          // Always navigate to edit, permissions should be enforced server‐side
          IconButton(
            icon: const Icon(Icons.edit),
            onPressed: () => Navigator.pushNamed(
              context,
              '/edit-task',
              arguments: task,
            ),
          ),
          IconButton(
            icon: const Icon(Icons.delete),
            onPressed: () async {
              final ok = await ApiService().deleteTask(task.id);
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
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: ListView(
          children: [
            Text('Task Type: ${task.taskType}', style: const TextStyle(fontSize: 18)),
            const SizedBox(height: 8),
            Text('Title: ${task.title}', style: const TextStyle(fontSize: 18)),
            const SizedBox(height: 8),
            Text('Description: ${task.description}', style: const TextStyle(fontSize: 16)),
            const Divider(height: 32),
            Text('Property: ${task.propertyName}', style: const TextStyle(fontSize: 16)),
            const SizedBox(height: 8),
            Text('Status: ${task.status}', style: const TextStyle(fontSize: 16)),
            const SizedBox(height: 8),
            Text('Created by: ${task.createdBy ?? "unknown"}', style: const TextStyle(fontSize: 16)),
            const SizedBox(height: 8),
            Text(
              'Assigned to: ${task.assignedToUsername ?? "Not assigned"}',
              style: const TextStyle(fontSize: 16),
            ),
            const SizedBox(height: 8),
            Text('Modified by: ${task.modifiedBy ?? "n/a"}',
                style: const TextStyle(fontSize: 16)),
            const Divider(height: 32),
            const Text('History:', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            if (task.history.isEmpty)
              const Text('No history available', style: TextStyle(fontSize: 16))
            else
              ...task.history.map(
                (entry) => Padding(
                  padding: const EdgeInsets.symmetric(vertical: 4),
                  child: Text('• $entry', style: const TextStyle(fontSize: 16)),
                ),
              ),
          ],
        ),
      ),
    );
  }
}