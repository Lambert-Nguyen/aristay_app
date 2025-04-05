import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

class TaskFormScreen extends StatefulWidget {
  const TaskFormScreen({Key? key}) : super(key: key);

  @override
  State<TaskFormScreen> createState() => _TaskFormScreenState();
}

class _TaskFormScreenState extends State<TaskFormScreen> {
  final _formKey = GlobalKey<FormState>();
  final TextEditingController _propertyNameController = TextEditingController();
  String _status = 'pending'; // default status
  bool _isLoading = false;
  String? _errorMessage;

  Future<void> _createTask() async {
    if (_formKey.currentState!.validate()) {
      setState(() {
        _isLoading = true;
        _errorMessage = null;
      });

      try {
        // Retrieve the stored token
        final prefs = await SharedPreferences.getInstance();
        final token = prefs.getString('auth_token');
        if (token == null) {
          setState(() {
            _errorMessage = 'Authentication token not found.';
          });
          return;
        }

        final url = Uri.parse('http://192.168.1.41:8000/api/cleaning-tasks/');
        final response = await http.post(
          url,
          headers: {
            'Authorization': 'Token $token',
            'Content-Type': 'application/json',
          },
          body: jsonEncode({
            'property_name': _propertyNameController.text,
            'status': _status,
          }),
        );

        if (response.statusCode == 201 || response.statusCode == 200) {
          // Task created successfully; pop this screen to return to the task list.
          Navigator.pop(context, true);
        } else {
          setState(() {
            _errorMessage = 'Failed to create task. Status: ${response.statusCode}';
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
      appBar: AppBar(title: const Text('Create New Task')),
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
                      onPressed: _createTask,
                      child: const Text('Create Task'),
                    ),
            ],
          ),
        ),
      ),
    );
  }
}