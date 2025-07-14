import 'dart:io';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import '../models/property.dart';
import '../services/api_service.dart';

class TaskFormScreen extends StatefulWidget {
  const TaskFormScreen({Key? key}) : super(key: key);

  @override
  State<TaskFormScreen> createState() => _TaskFormScreenState();
}

class _TaskFormScreenState extends State<TaskFormScreen> {
  final _formKey = GlobalKey<FormState>();
  final _titleCtrl = TextEditingController();
  final _descCtrl = TextEditingController();

  List<Property> _properties = [];
  Property? _selectedProperty;
  String _taskType = 'cleaning';
  String _status = 'pending';
  File? _pickedImage;

  bool _loading = false;
  String? _error;
  Map<String, String> _fieldErrors = {};

  @override
  void initState() {
    super.initState();
    ApiService()
        .fetchProperties()
        .then((list) => setState(() => _properties = list))
        .catchError((_) => setState(() => _error = 'Failed to load properties'));
  }

  Future<void> _pickImage() async {
    final picker = ImagePicker();
    final picked = await picker.pickImage(source: ImageSource.gallery);
    if (picked != null) setState(() => _pickedImage = File(picked.path));
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate() || _selectedProperty == null) return;

    setState(() {
      _loading = true;
      _error = null;
      _fieldErrors.clear();
    });

    try {
      final created = await ApiService().createTask({
        'property': _selectedProperty!.id,
        'task_type': _taskType,
        'title': _titleCtrl.text.trim(),
        'description': _descCtrl.text.trim(),
        'status': _status,
      });

      final int newTaskId = created['id'] as int;
      if (_pickedImage != null) {
        await ApiService().uploadTaskImage(newTaskId, _pickedImage!);
      }

      Navigator.pop(context, true);
    } on ValidationException catch (ve) {
      setState(() => _fieldErrors = ve.errors);
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_properties.isEmpty) {
      return Scaffold(
        appBar: AppBar(title: const Text('New Task')),
        body: Center(
          child: _error != null
              ? Text(_error!, style: const TextStyle(color: Colors.red))
              : const CircularProgressIndicator(),
        ),
      );
    }

    return Scaffold(
      appBar: AppBar(title: const Text('New Task')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Form(
          key: _formKey,
          child: ListView(
            children: [
              DropdownButtonFormField<Property>(
                decoration: InputDecoration(
                  labelText: 'Property',
                  errorText: _fieldErrors['property'],
                ),
                items: _properties
                    .map((p) => DropdownMenuItem(value: p, child: Text(p.name)))
                    .toList(),
                onChanged: (p) => setState(() => _selectedProperty = p),
                validator: (p) => p == null ? 'Pick one' : null,
              ),

              const SizedBox(height: 16),
              DropdownButtonFormField<String>(
                decoration: InputDecoration(
                  labelText: 'Task Type',
                  errorText: _fieldErrors['task_type'],
                ),
                value: _taskType,
                items: ['cleaning', 'maintenance']
                    .map((t) => DropdownMenuItem(value: t, child: Text(t)))
                    .toList(),
                onChanged: (v) => setState(() => _taskType = v!),
              ),

              const SizedBox(height: 16),
              TextFormField(
                controller: _titleCtrl,
                decoration: InputDecoration(
                  labelText: 'Title',
                  errorText: _fieldErrors['title'],
                ),
                validator: (v) => v!.trim().isEmpty ? 'Required' : null,
              ),

              const SizedBox(height: 16),
              TextFormField(
                controller: _descCtrl,
                decoration: InputDecoration(
                  labelText: 'Description',
                  errorText: _fieldErrors['description'],
                ),
                maxLines: 3,
              ),

              const SizedBox(height: 16),
              DropdownButtonFormField<String>(
                decoration: InputDecoration(
                  labelText: 'Status',
                  errorText: _fieldErrors['status'],
                ),
                value: _status,
                items: ['pending', 'in-progress', 'completed', 'canceled']
                    .map((s) => DropdownMenuItem(value: s, child: Text(s)))
                    .toList(),
                onChanged: (v) => setState(() => _status = v!),
              ),

              const SizedBox(height: 16),
              TextButton.icon(
                icon: const Icon(Icons.photo),
                label: const Text('Attach Photo'),
                onPressed: _pickImage,
              ),
              if (_pickedImage != null)
                Padding(
                  padding: const EdgeInsets.only(top: 8),
                  child: Image.file(_pickedImage!, height: 100),
                ),

              const SizedBox(height: 24),
              if (_error != null)
                Text(_error!, style: const TextStyle(color: Colors.red)),

              _loading
                  ? const Center(child: CircularProgressIndicator())
                  : ElevatedButton(onPressed: _submit, child: const Text('Create')),
            ],
          ),
        ),
      ),
    );
  }

  @override
  void dispose() {
    _titleCtrl.dispose();
    _descCtrl.dispose();
    super.dispose();
  }
}