import 'dart:io';

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import '../models/property.dart';
import '../models/task.dart';
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
  String _status = 'pending';

  bool _loading = true;
  bool _saving = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _titleCtrl = TextEditingController(text: widget.task.title);
    _descCtrl = TextEditingController(text: widget.task.description);
    _taskType = widget.task.taskType;
    _status = widget.task.status;
    _loadDropdowns();
  }

  Future<void> _loadDropdowns() async {
    setState(() => _loading = true);
    try {
      final props = await ApiService().fetchProperties();
      final users = await ApiService().fetchUsers();
      final selProp = props.firstWhere(
        (p) => p.id == widget.task.propertyId,
        orElse: () => props.first,
      );
      User? selUser;
      if (widget.task.assignedToId != null) {
        selUser = users.firstWhere(
          (u) => u.id == widget.task.assignedToId,
          orElse: () => users.first,
        );
      }
      setState(() {
        _properties = props;
        _users = users;
        _selectedProperty = selProp;
        _selectedAssignee = selUser;
        _error = null;
      });
    } catch (e) {
      setState(() => _error = 'Load failed: $e');
    } finally {
      setState(() => _loading = false);
    }
  }

  Future<void> _save() async {
    // guard against no‐property selected
    if (_selectedProperty == null) {
      setState(() {
        _error = 'Please choose a property before saving.';
      });
      return;
    }
    // now safe to validate
    if (!_formKey.currentState!.validate()) return;

    setState(() {
      _saving = true;
      _error = null;
    });

    final payload = {
      'property': _selectedProperty!.id,
      'task_type': _taskType,
      'title': _titleCtrl.text,
      'description': _descCtrl.text,
      'status': _status,
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

  Future<void> _deleteImage(int imageId) async {
    setState(() => _loading = true);
    try {
      await ApiService().deleteTaskImage(widget.task.id, imageId);
      final updated = await ApiService().fetchTask(widget.task.id);
      setState(() {
        widget.task.imageUrls
          ..clear()
          ..addAll(updated.imageUrls);
        widget.task.imageIds
          ..clear()
          ..addAll(updated.imageIds);
        widget.task.history
          ..clear()
          ..addAll(updated.history);
      });
    } catch (e) {
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text('Delete failed: $e')));
    } finally {
      setState(() => _loading = false);
    }
  }

  Future<void> _replaceImage(int imageId) async {
    final picker = ImagePicker();
    final picked = await picker.pickImage(source: ImageSource.gallery);
    if (picked == null) return;

    setState(() => _loading = true);
    try {
      await ApiService().deleteTaskImage(widget.task.id, imageId);
      await ApiService().uploadTaskImage(
          widget.task.id, File(picked.path));
      final updated = await ApiService().fetchTask(widget.task.id);
      setState(() {
        widget.task.imageUrls
          ..clear()
          ..addAll(updated.imageUrls);
        widget.task.imageIds
          ..clear()
          ..addAll(updated.imageIds);
        widget.task.history
          ..clear()
          ..addAll(updated.history);
      });
    } catch (e) {
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text('Replace failed: $e')));
    } finally {
      setState(() => _loading = false);
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
              // API error message
              if (_error != null)
                Padding(
                  padding: const EdgeInsets.only(bottom: 8.0),
                  child: Text(
                    _error!,
                    style: const TextStyle(color: Colors.red),
                  ),
                ),
              // Property
              DropdownButtonFormField<Property>(
                decoration: const InputDecoration(labelText: 'Property'),
                value: _selectedProperty,
                items: _properties
                    .map((p) => DropdownMenuItem(
                          value: p,
                          child: Text(p.name),
                        ))
                    .toList(),
                validator: (p) => p == null ? 'Choose a property' : null,
                onChanged: (p) => setState(() => _selectedProperty = p),
              ),
              const SizedBox(height: 16),
              // Task Type
              DropdownButtonFormField<String>(
                decoration: const InputDecoration(labelText: 'Task Type'),
                value: _taskType,
                items: ['cleaning', 'maintenance']
                    .map((t) => DropdownMenuItem(
                          value: t,
                          child: Text(t),
                        ))
                    .toList(),
                onChanged: (v) => setState(() => _taskType = v!),
              ),
              const SizedBox(height: 16),
              // Title
              TextFormField(
                controller: _titleCtrl,
                decoration: const InputDecoration(labelText: 'Title'),
                validator: (v) => v!.isEmpty ? 'Required' : null,
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
                    .map((s) => DropdownMenuItem(
                          value: s,
                          child: Text(s),
                        ))
                    .toList(),
                onChanged: (v) => setState(() => _status = v!),
              ),
              const SizedBox(height: 16),
              // Assignee
              DropdownButtonFormField<User>(
                decoration: const InputDecoration(labelText: 'Assign to'),
                value: _selectedAssignee,
                items: _users
                    .map((u) => DropdownMenuItem(
                          value: u,
                          child: Text(u.username),
                        ))
                    .toList(),
                validator: (u) => u == null ? 'Required' : null,
                onChanged: (u) => setState(() => _selectedAssignee = u),
              ),
              const SizedBox(height: 24),
              // Photos
              const Text('Photos',
                  style: TextStyle(fontWeight: FontWeight.bold)),
              const SizedBox(height: 8),
              if (widget.task.imageUrls.isEmpty)
                const Text('No photos attached')
              else
                SizedBox(
                  height: 100,
                  child: ListView.builder(
                    scrollDirection: Axis.horizontal,
                    itemCount: widget.task.imageUrls.length,
                    itemBuilder: (_, i) {
                      final url = widget.task.imageUrls[i];
                      final imageId = widget.task.imageIds[i];
                      return Padding(
                        padding: const EdgeInsets.only(right: 8),
                        child: Stack(
                          children: [
                            Image.network(url,
                                height: 100, fit: BoxFit.cover),
                            Positioned(
                              right: 0,
                              child: Column(
                                children: [
                                  IconButton(
                                    icon: const Icon(
                                        Icons.delete, color: Colors.red),
                                    onPressed: () =>
                                        _deleteImage(imageId),
                                  ),
                                  IconButton(
                                    icon: const Icon(Icons.refresh),
                                    onPressed: () =>
                                        _replaceImage(imageId),
                                  ),
                                ],
                              ),
                            ),
                          ],
                        ),
                      );
                    },
                  ),
                ),
              const SizedBox(height: 24),
              // Save
              _saving
                  ? const Center(
                      child: CircularProgressIndicator(),
                    )
                  : ElevatedButton(
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