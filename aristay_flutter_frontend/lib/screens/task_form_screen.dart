import 'package:flutter/material.dart';
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
  String _taskType = 'cleaning';
  final _titleCtrl = TextEditingController();
  final _descCtrl = TextEditingController();
  String _status = 'pending';
  bool _loading = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    ApiService().fetchProperties().then((l) => setState(() => _properties = l))
      .catchError((e) => setState(() => _error = 'Properties load failed'));
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate() || _selectedProperty == null) return;
    setState(() { _loading = true; _error = null; });
    final ok = await ApiService().createTask({
      'property': _selectedProperty!.id,
      'task_type': _taskType,
      'title': _titleCtrl.text,
      'description': _descCtrl.text,
      'status': _status,
    });
    setState(() => _loading = false);
    if (ok) Navigator.pop(context, true);
    else setState(() => _error = 'Create failed');
  }

  @override
  Widget build(BuildContext context) {
    if (_properties.isEmpty) {
      return Scaffold(
        appBar: AppBar(title: const Text('New Task')),
        body: Center(child: _error != null ? Text(_error!) : const CircularProgressIndicator()),
      );
    }

    return Scaffold(
      appBar: AppBar(title: const Text('New Task')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Form(
          key: _formKey,
          child: ListView(children: [
            DropdownButtonFormField<Property>(
              decoration: const InputDecoration(labelText: 'Property'),
              items: _properties
                  .map((p) => DropdownMenuItem(value: p, child: Text(p.name)))
                  .toList(),
              onChanged: (p) => setState(() => _selectedProperty = p),
              validator: (p) => p == null ? 'Pick one' : null,
            ),
            const SizedBox(height: 16),
            DropdownButtonFormField<String>(
              decoration: const InputDecoration(labelText: 'Task Type'),
              value: _taskType,
              items: ['cleaning', 'maintenance']
                  .map((t) => DropdownMenuItem(value: t, child: Text(t)))
                  .toList(),
              onChanged: (v) => setState(() => _taskType = v!),
            ),
            const SizedBox(height: 16),
            TextFormField(
              controller: _titleCtrl,
              decoration: const InputDecoration(labelText: 'Title'),
              validator: (v) => v!.isEmpty ? 'Required' : null,
            ),
            const SizedBox(height: 16),
            TextFormField(
              controller: _descCtrl,
              decoration: const InputDecoration(labelText: 'Description'),
              maxLines: 3,
            ),
            const SizedBox(height: 16),
            DropdownButtonFormField<String>(
              decoration: const InputDecoration(labelText: 'Status'),
              value: _status,
              items: ['pending', 'in-progress', 'completed', 'canceled']
                  .map((s) => DropdownMenuItem(value: s, child: Text(s)))
                  .toList(),
              onChanged: (v) => setState(() => _status = v!),
            ),
            const SizedBox(height: 24),
            if (_error != null) Text(_error!, style: const TextStyle(color: Colors.red)),
            _loading
                ? const Center(child: CircularProgressIndicator())
                : ElevatedButton(onPressed: _submit, child: const Text('Create')),
          ]),
        ),
      ),
    );
  }
}