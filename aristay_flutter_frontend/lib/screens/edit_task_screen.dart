import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../services/api_service.dart';

class EditTaskScreen extends StatefulWidget {
  final Map<String, dynamic> task; // The task to be edited

  const EditTaskScreen({Key? key, required this.task}) : super(key: key);

  @override
  _EditTaskScreenState createState() => _EditTaskScreenState();
}

class _EditTaskScreenState extends State<EditTaskScreen> {
  final _formKey = GlobalKey<FormState>();
  late TextEditingController _propertyNameController;
  late String _status;
  bool _isLoading = false;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    // Initialize the form controllers with the existing task data
    _propertyNameController = TextEditingController(text: widget.task['property_name']);
    _status = widget.task['status'] ?? 'pending';
  }

  Future<void> _updateTask() async {
    if (_formKey.currentState!.validate()) {
      setState(() {
        _isLoading = true;
        _errorMessage = null;
      });

      try {
        final apiService = ApiService();
        // Prepare updated data; you can update additional fields if needed
        final updatedData = {
          'property_name': _propertyNameController.text,
          'status': _status,
        };

        bool success = await apiService.updateCleaningTask(widget.task['id'], updatedData);
        if (success) {
          // If update is successful, pop and indicate a refresh is needed
          Navigator.pop(context, true);
        } else {
          setState(() {
            _errorMessage = 'Failed to update task.';
          });
        }
      } catch (e) {
        setState(() {
          _errorMessage = 'Error: $e';
        });
      } finally {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  @override
  void dispose() {
    _propertyNameController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Edit Task')),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Form(
          key: _formKey,
          child: Column(
            children: [
              TextFormField(
                controller: _propertyNameController,
                decoration: const InputDecoration(labelText: 'Property Name'),
                validator: (value) =>
                    value == null || value.isEmpty ? 'Please enter a property name' : null,
              ),
              const SizedBox(height: 16),
              DropdownButtonFormField<String>(
                value: _status,
                decoration: const InputDecoration(labelText: 'Status'),
                items: ['pending', 'completed']
                    .map((status) => DropdownMenuItem(
                          value: status,
                          child: Text(status),
                        ))
                    .toList(),
                onChanged: (value) {
                  setState(() {
                    _status = value ?? 'pending';
                  });
                },
              ),
              const SizedBox(height: 24),
              if (_errorMessage != null)
                Text(_errorMessage!, style: const TextStyle(color: Colors.red)),
              _isLoading
                  ? const CircularProgressIndicator()
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