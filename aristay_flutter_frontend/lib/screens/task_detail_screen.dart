import 'package:flutter/material.dart';
import '../models/task.dart';
import '../services/api_service.dart';

class TaskDetailScreen extends StatelessWidget {
  final Task task;
  const TaskDetailScreen({Key? key, required this.task}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Task Details'),
        actions: [
          // Only show edit button if current user matches createdBy
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
              if (ok) Navigator.popUntil(context, ModalRoute.withName('/tasks'));
            },
          )
        ],
      ),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: ListView(children: [
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
          Text('Created by: ${task.createdBy}', style: const TextStyle(fontSize: 16)),
          const SizedBox(height: 8),
          Text('Assigned to: ${task.assignedTo}', style: const TextStyle(fontSize: 16)),
          const SizedBox(height: 8),
          Text('Modified by: ${task.modifiedBy}', style: const TextStyle(fontSize: 16)),
          const Divider(height: 32),
          const Text('History:', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
          ...task.history.map((h) => Padding(
                padding: const EdgeInsets.symmetric(vertical: 4),
                child: Text('• $h'),
              )),
        ]),
      ),
    );
  }
}