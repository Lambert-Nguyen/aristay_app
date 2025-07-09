import 'package:flutter/material.dart';
import '../models/task.dart';
import '../models/property.dart';
import '../services/api_service.dart';

class EditTaskScreen extends StatefulWidget {
  final Task task;
  const EditTaskScreen({Key? key, required this.task}) : super(key: key);
  @override
  State<EditTaskScreen> createState() => _EditTaskScreenState();
}

class _EditTaskScreenState extends State<EditTaskScreen> {
  final _formKey = GlobalKey<FormState>();
  List<Property> _properties = [];
  Property? _selectedProperty;
  late String _taskType, _status;
  final _titleCtrl = TextEditingController();
  final _descCtrl = TextEditingController();
  bool _loading = false, _error = false;

  @override
  void initState() {
    super.initState();
    _taskType = widget.task.taskType;
    _status = widget.task.status;
    _titleCtrl.text = widget.task.title;
    _descCtrl.text = widget.task.description;
    ApiService()
        .fetchProperties()
        .then((l) {
          _properties = l;
          _selectedProperty = l.firstWhere((p) => p.id == widget.task.propertyId);
          setState(() {});
        })
        .catchError((_) => setState(() => _error = true));
  }

  Future<void> _save() async {
    if (!_formKey.currentState!.validate() || _selectedProperty == null) return;
    setState(() => _loading = true);
    final ok = await ApiService().updateTask(widget.task.id, {
      'property': _selectedProperty!.id,
      'task_type': _taskType,
      'title': _titleCtrl.text,
      'description': _descCtrl.text,
      'status': _status,
    });
    setState(() => _loading = false);
    if (ok) Navigator.pop(context, true);
    else ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Update failed')));
  }

  @override
  Widget build(BuildContext context) {
    if (_properties.isEmpty && !_error) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }

    return Scaffold(
      appBar: AppBar(title: const Text('Edit Task')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Form(
          key: _formKey,
          child: ListView(children: [
            DropdownButtonFormField<Property>(
              decoration: const InputDecoration(labelText: 'Property'),
              value: _selectedProperty,
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
            _loading
                ? const Center(child: CircularProgressIndicator())
                : ElevatedButton(onPressed: _save, child: const Text('Save')),
          ]),
        ),
      ),
    );
  }
}