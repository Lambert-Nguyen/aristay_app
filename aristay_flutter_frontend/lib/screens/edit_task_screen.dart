// lib/screens/edit_task_screen.dart

import 'package:flutter/material.dart';
import '../models/task.dart';
import '../services/api_service.dart';

class EditTaskScreen extends StatefulWidget {
  final Task task;

  const EditTaskScreen({Key? key, required this.task}) : super(key: key);

  @override
  State<EditTaskScreen> createState() => _EditTaskScreenState();
}

class _EditTaskScreenState extends State<EditTaskScreen> {
  final _formKey = GlobalKey<FormState>();
  late String _status;
  bool _isLoading = false;
  String? _errorMessage;

  final List<String> _allowedStatuses = [
    'pending',
    'in-progress',
    'completed',
    'canceled',
  ];

  @override
  void initState() {
    super.initState();
    // initialize dropdown to the task’s current status (default to 'pending')
    _status = _allowedStatuses.contains(widget.task.status)
        ? widget.task.status
        : 'pending';
  }

  Future<void> _updateTask() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final api = ApiService();
      final success = await api.updateCleaningTask(
        widget.task.id,
        { 'status': _status },        // only send status
      );
      if (success) {
        Navigator.pop(context, true);
      } else {
        setState(() => _errorMessage = 'Failed to update task.');
      }
    } catch (e) {
      setState(() => _errorMessage = 'Error: $e');
    } finally {
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Edit Task')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Read-only display of the property name
              Text(
                'Property: ${widget.task.propertyName}',
                style: const TextStyle(fontSize: 16),
              ),
              const SizedBox(height: 24),

              // Status dropdown
              DropdownButtonFormField<String>(
                value: _status,
                decoration: const InputDecoration(labelText: 'Status'),
                items: _allowedStatuses
                    .map((s) => DropdownMenuItem(value: s, child: Text(s)))
                    .toList(),
                onChanged: (v) => setState(() => _status = v ?? _status),
                validator: (v) =>
                    v == null || v.isEmpty ? 'Please select a status' : null,
              ),
              const SizedBox(height: 24),

              if (_errorMessage != null)
                Text(_errorMessage!, style: const TextStyle(color: Colors.red)),
              const SizedBox(height: 8),

              _isLoading
                  ? const Center(child: CircularProgressIndicator())
                  : ElevatedButton(
                      onPressed: _updateTask,
                      child: const Text('Update Task'),
                    ),
            ],
          ),
        ),
      ),
    );
  }
}