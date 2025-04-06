import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

class TaskDetailScreen extends StatefulWidget {
  final Map<String, dynamic> task;

  const TaskDetailScreen({Key? key, required this.task}) : super(key: key);

  @override
  _TaskDetailScreenState createState() => _TaskDetailScreenState();
}

class _TaskDetailScreenState extends State<TaskDetailScreen> {
  String? _currentUsername;
  bool _canEdit = false;

  @override
  void initState() {
    super.initState();
    _loadCurrentUser();
  }

  Future<void> _loadCurrentUser() async {
    final prefs = await SharedPreferences.getInstance();
    // Ensure that you save the username during login (e.g., under the key "username")
    final storedUsername = prefs.getString('username');
    setState(() {
      _currentUsername = storedUsername;
      // Compare in a normalized way (trim and lowercase) for accuracy.
      _canEdit = (widget.task['created_by']?.toString().trim().toLowerCase() ==
          (storedUsername ?? '').trim().toLowerCase());
    });
  }

  @override
  Widget build(BuildContext context) {
    final propertyName = widget.task['property_name'] ?? 'Unnamed';
    final status = widget.task['status'] ?? 'unknown';
    final createdBy = widget.task['created_by'] ?? 'unknown';
    final assignedTo = widget.task['assigned_to'] ?? 'Not assigned';
    // Assume history is returned as a List from the backend serializer.
    final history = widget.task['history'] is List ? widget.task['history'] as List<dynamic> : [];

    return Scaffold(
      appBar: AppBar(
        title: const Text('Task Details'),
        actions: [
          if (_canEdit)
            IconButton(
              icon: const Icon(Icons.edit),
              onPressed: () {
                // Navigate to edit screen if the user can edit.
                Navigator.pushNamed(context, '/edit-task', arguments: widget.task);
              },
            )
        ],
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: ListView(
          children: [
            Text('Property: $propertyName', style: const TextStyle(fontSize: 18)),
            const SizedBox(height: 8),
            Text('Status: $status', style: const TextStyle(fontSize: 16)),
            const SizedBox(height: 8),
            Text('Created by: $createdBy', style: const TextStyle(fontSize: 16)),
            const SizedBox(height: 8),
            Text('Assigned to: $assignedTo', style: const TextStyle(fontSize: 16)),
            const SizedBox(height: 16),
            const Text('Task History:', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            history.isNotEmpty
                ? Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: history
                        .map((entry) => Text('• $entry', style: const TextStyle(fontSize: 16)))
                        .toList(),
                  )
                : const Text('No history available', style: TextStyle(fontSize: 16)),
          ],
        ),
      ),
    );
  }
}