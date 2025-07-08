import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/property.dart';
import '../services/api_service.dart';

class TaskFormScreen extends StatefulWidget {
  const TaskFormScreen({Key? key}) : super(key: key);

  @override
  State<TaskFormScreen> createState() => _TaskFormScreenState();
}

class _TaskFormScreenState extends State<TaskFormScreen> {
  final _formKey = GlobalKey<FormState>();
  List<Property> _properties = [];
  Property? _selectedProperty;
  String _status = 'pending'; // default status
  bool _isLoading = false;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    ApiService().fetchProperties().then((list) {
      setState(() {
        _properties = list;
        if (_properties.isNotEmpty) {
          _selectedProperty = _properties.first;
        }
      });
    }).catchError((e) {
      setState(() {
        _errorMessage = 'Failed to load properties: $e';
      });
    });
  }

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

        final api = ApiService();
        final success = await api.createTask({
          'property': _selectedProperty!.id,
          'status': _status,
        });
        if (success) {
          Navigator.pop(context, true);
        } else {
          setState(() {
            _errorMessage = 'Failed to create task.';
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
              DropdownButtonFormField<Property>(
                value: _selectedProperty,
                decoration: const InputDecoration(labelText: 'Property'),
                items: _properties.map((prop) {
                  return DropdownMenuItem<Property>(
                    value: prop,
                    child: Text(prop.name),
                  );
                }).toList(),
                onChanged: (newProp) {
                  setState(() {
                    _selectedProperty = newProp;
                  });
                },
                validator: (value) => value == null ? 'Please select a property' : null,
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