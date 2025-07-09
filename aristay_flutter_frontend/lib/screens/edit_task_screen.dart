import 'package:flutter/material.dart';
import '../models/task.dart';
import '../models/property.dart';
import '../models/user.dart';
import '../services/api_service.dart';

class EditTaskScreen extends StatefulWidget {
  final Task task;
  const EditTaskScreen({Key? key, required this.task}) : super(key: key);

  @override
  State<EditTaskScreen> createState() => _EditTaskScreenState();
}

class _EditTaskScreenState extends State<EditTaskScreen> {
  final _formKey = GlobalKey<FormState>();
  late TextEditingController _titleCtrl;
  late TextEditingController _descCtrl;

  List<Property> _properties = [];
  Property? _selectedProperty;

  List<User> _users = [];
  User? _selectedAssignee;

  String _taskType = 'cleaning';
  String _status   = 'pending';

  bool _loading = true;
  bool _saving  = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _titleCtrl = TextEditingController(text: widget.task.title);
    _descCtrl  = TextEditingController(text: widget.task.description);
    _taskType  = widget.task.taskType;
    _status    = widget.task.status;
    _loadAll();
  }

  Future<void> _loadAll() async {
    setState(() => _loading = true);
    try {
      // Fetch dropdown data
      final props = await ApiService().fetchProperties();
      final users = await ApiService().fetchUsers();

      // Select the property matching this task (fallback to first)
      final selProp = props.firstWhere(
        (p) => p.id == widget.task.propertyId,
        orElse: () => props.first,
      );

      // Safely pick the current assignee by ID, if any
      User? selUser;
      final assignedId = widget.task.assignedToId;
      if (assignedId != null) {
        final matches = users.where((u) => u.id == assignedId).toList();
        if (matches.isNotEmpty) {
          selUser = matches.first;
        }
      }

      setState(() {
        _properties       = props;
        _users            = users;
        _selectedProperty = selProp;
        _selectedAssignee = selUser;
        _error            = null;
      });
    } catch (e) {
      setState(() => _error = 'Load failed: $e');
    } finally {
      setState(() => _loading = false);
    }
  }

  Future<void> _save() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() {
      _saving = true;
      _error  = null;
    });

    final payload = {
      'property':    _selectedProperty!.id,
      'task_type':   _taskType,
      'title':       _titleCtrl.text,
      'description': _descCtrl.text,
      'status':      _status,
      'assigned_to': _selectedAssignee?.id,
    };

    try {
      final ok = await ApiService().updateTask(widget.task.id, payload);
      if (ok) {
        Navigator.pop(context, true);
      } else {
        setState(() => _error = 'Save failed');
      }
    } catch (e) {
      setState(() => _error = 'Error: $e');
    } finally {
      setState(() => _saving = false);
    }
  }

  @override
  void dispose() {
    _titleCtrl.dispose();
    _descCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return const Scaffold(
        body: Center(child: CircularProgressIndicator()),
      );
    }
    if (_error != null) {
      return Scaffold(
        appBar: AppBar(title: const Text('Edit Task')),
        body: Center(child: Text(_error!)),
      );
    }

    return Scaffold(
      appBar: AppBar(title: const Text('Edit Task')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Form(
          key: _formKey,
          child: ListView(
            children: [
              // Property dropdown
              DropdownButtonFormField<Property>(
                decoration: const InputDecoration(labelText: 'Property'),
                value: _selectedProperty,
                items: _properties
                    .map((p) => DropdownMenuItem(value: p, child: Text(p.name)))
                    .toList(),
                onChanged: (p) => setState(() => _selectedProperty = p),
                validator: (p) => p == null ? 'Select a property' : null,
              ),
              const SizedBox(height: 16),

              // Task type
              DropdownButtonFormField<String>(
                decoration: const InputDecoration(labelText: 'Task Type'),
                value: _taskType,
                items: ['cleaning', 'maintenance']
                    .map((t) => DropdownMenuItem(value: t, child: Text(t)))
                    .toList(),
                onChanged: (t) => setState(() => _taskType = t!),
              ),
              const SizedBox(height: 16),

              // Title
              TextFormField(
                controller: _titleCtrl,
                decoration: const InputDecoration(labelText: 'Title'),
                validator: (v) => (v ?? '').isEmpty ? 'Enter a title' : null,
              ),
              const SizedBox(height: 16),

              // Description
              TextFormField(
                controller: _descCtrl,
                decoration: const InputDecoration(labelText: 'Description'),
                maxLines: 3,
              ),
              const SizedBox(height: 16),

              // Status
              DropdownButtonFormField<String>(
                decoration: const InputDecoration(labelText: 'Status'),
                value: _status,
                items: ['pending', 'in-progress', 'completed', 'canceled']
                    .map((s) => DropdownMenuItem(value: s, child: Text(s)))
                    .toList(),
                onChanged: (s) => setState(() => _status = s!),
              ),
              const SizedBox(height: 16),

              // Assigned to
              DropdownButtonFormField<User>(
                decoration: const InputDecoration(labelText: 'Assign to'),
                value: _selectedAssignee,
                items: _users
                    .map((u) => DropdownMenuItem(value: u, child: Text(u.username)))
                    .toList(),
                onChanged: (u) => setState(() => _selectedAssignee = u),
                validator: (u) => u == null ? 'Select an assignee' : null,
              ),
              const SizedBox(height: 24),

              if (_saving)
                const Center(child: CircularProgressIndicator())
              else
                ElevatedButton(
                  onPressed: _save,
                  child: const Text('Save Changes'),
                ),
            ],
          ),
        ),
      ),
    );
  }
}