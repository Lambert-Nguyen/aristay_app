// lib/screens/edit_task_screen.dart

import 'dart:io';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:intl/intl.dart';

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

  // controllers
  late final TextEditingController _titleCtrl;
  late final TextEditingController _descCtrl;

  // dropdown sources + selections
  List<Property> _properties = [];
  Property? _selectedProperty;

  List<User> _users = [];
  User? _selectedAssignee;

  String _taskType = 'cleaning';
  String _status = 'pending';

  // ui state
  bool _loading = true;
  bool _saving  = false;
  String? _error;
  Map<String, String> _fieldErrors = {};

  // helpers
  final _dateFmt = DateFormat('yyyy-MM-dd HH:mm:ss');

  List<String> get _statusOptions =>
      const ['pending', 'in-progress', 'completed', 'canceled'];
  List<String> get _taskTypeOptions =>
      const ['cleaning', 'maintenance'];

  @override
  void initState() {
    super.initState();
    _titleCtrl = TextEditingController(text: widget.task.title);
    _descCtrl  = TextEditingController(text: widget.task.description);
    _taskType  = widget.task.taskType;
    _status    = widget.task.status;
    _loadDropdowns();
  }

  Future<void> _loadDropdowns() async {
  setState(() => _loading = true);
  try {
    final props     = await ApiService().fetchProperties();
    final usersResp = await ApiService().fetchUsers();
    final users     = usersResp['results'] as List<User>;

    // pick property (nullable-safe)
    Property? selProp;
    try {
      selProp = props.firstWhere((p) => p.id == widget.task.propertyId);
    } catch (_) {
      selProp = props.isNotEmpty ? props.first : null;
    }

    // pick assignee (nullable-safe)
    User? selUser;
    if (widget.task.assignedToId != null) {
      try {
        selUser = users.firstWhere((u) => u.id == widget.task.assignedToId);
      } catch (_) {
        selUser = users.isNotEmpty ? users.first : null;
      }
    }

    setState(() {
      _properties        = props;
      _users             = users;
      _selectedProperty  = selProp;
      _selectedAssignee  = selUser;
      _error             = null;
    });
  } catch (e) {
    setState(() => _error = 'Load failed: $e');
  } finally {
    setState(() => _loading = false);
  }
}

  String _fmtLocal(DateTime utc) {
    final local = utc.toLocal();
    return '${_dateFmt.format(local)} ${local.timeZoneName}';
  }

  Future<void> _save() async {
    if (_selectedProperty == null) {
      setState(() => _error = 'Please choose a property');
      return;
    }
    if (!_formKey.currentState!.validate()) return;

    setState(() {
      _saving = true;
      _error = null;
      _fieldErrors.clear();
    });

    final payload = {
      'property': _selectedProperty!.id,
      'task_type': _taskType,
      'title': _titleCtrl.text.trim(),
      'description': _descCtrl.text.trim(),
      'status': _status,
      'assigned_to': _selectedAssignee?.id,
    };

    try {
      await ApiService().updateTask(widget.task.id, payload);
      if (!mounted) return;
      Navigator.pop(context, true);
    } on ValidationException catch (ve) {
      setState(() => _fieldErrors = ve.errors);
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(e.toString())),
      );
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  Future<void> _addPhoto() async {
    final picker = ImagePicker();
    final picked = await picker.pickImage(source: ImageSource.gallery);
    if (picked == null) return;

    setState(() => _loading = true);
    try {
      await ApiService().uploadTaskImage(widget.task.id, File(picked.path));
      final updated = await ApiService().fetchTask(widget.task.id);
      setState(() {
        widget.task.imageUrls
          ..clear()
          ..addAll(updated.imageUrls);
        widget.task.imageIds
          ..clear()
          ..addAll(updated.imageIds);
      });
      if (!mounted) return;
      ScaffoldMessenger.of(context)
          .showSnackBar(const SnackBar(content: Text('Photo added')));
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text(e.toString())));
    } finally {
      if (mounted) setState(() => _loading = false);
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
      });
      if (!mounted) return;
      ScaffoldMessenger.of(context)
          .showSnackBar(const SnackBar(content: Text('Photo deleted')));
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text(e.toString())));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _replaceImage(int imageId) async {
    final picker = ImagePicker();
    final picked = await picker.pickImage(source: ImageSource.gallery);
    if (picked == null) return;

    setState(() => _loading = true);
    try {
      await ApiService().deleteTaskImage(widget.task.id, imageId);
      await ApiService().uploadTaskImage(widget.task.id, File(picked.path));
      final updated = await ApiService().fetchTask(widget.task.id);
      setState(() {
        widget.task.imageUrls
          ..clear()
          ..addAll(updated.imageUrls);
        widget.task.imageIds
          ..clear()
          ..addAll(updated.imageIds);
      });
      if (!mounted) return;
      ScaffoldMessenger.of(context)
          .showSnackBar(const SnackBar(content: Text('Photo replaced')));
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text(e.toString())));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  // ────────────── UI blocks (cards) ──────────────

  Widget _summaryCard() {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Title + status
            Row(
              children: [
                Expanded(
                  child: Text(
                    _titleCtrl.text.isEmpty ? '(Untitled Task)' : _titleCtrl.text,
                    style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w700),
                  ),
                ),
                Chip(
                  label: Text(_status.replaceAll('-', ' ')),
                  backgroundColor: _statusColor(_status),
                  side: const BorderSide(color: Colors.black12),
                )
              ],
            ),
            const SizedBox(height: 8),
            // property / type / assignee
            Wrap(
              spacing: 12,
              runSpacing: 6,
              crossAxisAlignment: WrapCrossAlignment.center,
              children: [
                const Icon(Icons.home_outlined, size: 18),
                Text(_selectedProperty?.name ?? widget.task.propertyName),
                const SizedBox(width: 10),
                const Icon(Icons.build_outlined, size: 18),
                Text(_taskType),
                const SizedBox(width: 10),
                const Icon(Icons.person_outline, size: 18),
                Text(_selectedAssignee?.username ?? (widget.task.assignedToUsername ?? 'Not assigned')),
              ],
            ),
            const Divider(height: 24),
            Text('Created:  ${_fmtLocal(widget.task.createdAt)}',
                style: const TextStyle(fontSize: 12, color: Colors.grey)),
            Text('Modified: ${_fmtLocal(widget.task.modifiedAt)}',
                style: const TextStyle(fontSize: 12, color: Colors.grey)),
          ],
        ),
      ),
    );
  }

  Widget _coreFormCard() {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: AbsorbPointer(
          absorbing: _saving,
          child: Column(
            children: [
              // Property
              DropdownButtonFormField<Property>(
                decoration: InputDecoration(
                  labelText: 'Property',
                  errorText: _fieldErrors['property'],
                ),
                value: _selectedProperty,
                items: _properties
                    .map((p) => DropdownMenuItem(value: p, child: Text(p.name)))
                    .toList(),
                onChanged: (p) => setState(() => _selectedProperty = p),
                validator: (p) => p == null ? 'Required' : null,
              ),
              const SizedBox(height: 16),

              // Task type
              DropdownButtonFormField<String>(
                decoration: InputDecoration(
                  labelText: 'Task Type',
                  errorText: _fieldErrors['task_type'],
                ),
                value: _taskType,
                items: _taskTypeOptions
                    .map((t) => DropdownMenuItem(value: t, child: Text(t)))
                    .toList(),
                onChanged: (v) => setState(() => _taskType = v!),
              ),
              const SizedBox(height: 16),

              // Title
              TextFormField(
                controller: _titleCtrl,
                decoration: InputDecoration(
                  labelText: 'Title',
                  errorText: _fieldErrors['title'],
                ),
                validator: (v) => v!.trim().isEmpty ? 'Required' : null,
                onChanged: (_) => setState(() {}), // refresh summary title
              ),
              const SizedBox(height: 16),

              // Description
              TextFormField(
                controller: _descCtrl,
                decoration: InputDecoration(
                  labelText: 'Description',
                  errorText: _fieldErrors['description'],
                ),
                maxLines: 3,
              ),
              const SizedBox(height: 16),

              // Status
              DropdownButtonFormField<String>(
                decoration: InputDecoration(
                  labelText: 'Status',
                  errorText: _fieldErrors['status'],
                ),
                value: _status,
                items: _statusOptions
                    .map((s) => DropdownMenuItem(value: s, child: Text(s)))
                    .toList(),
                onChanged: (v) => setState(() => _status = v!),
              ),
              const SizedBox(height: 16),

              // Assignee
              DropdownButtonFormField<User>(
                decoration: InputDecoration(
                  labelText: 'Assign to',
                  errorText: _fieldErrors['assigned_to'],
                ),
                value: _selectedAssignee,
                items: _users
                    .map((u) => DropdownMenuItem(value: u, child: Text(u.username)))
                    .toList(),
                onChanged: (u) => setState(() => _selectedAssignee = u),
                validator: (u) => u == null ? 'Required' : null,
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _notificationsInfoCard() {
    // edit screen shows read-only notification state for context
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: ListTile(
        leading: Icon(widget.task.isMuted ? Icons.notifications_off : Icons.notifications),
        title: const Text('Notifications'),
        subtitle: Text(widget.task.isMuted ? 'Muted for you' : 'Enabled for you'),
        trailing: const Text('Read-only'),
      ),
    );
  }

  Widget _photosCard() {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.fromLTRB(16, 12, 16, 12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Expanded(
                  child: Text('Photos', style: TextStyle(fontWeight: FontWeight.bold)),
                ),
                TextButton.icon(
                  onPressed: _saving ? null : _addPhoto,
                  icon: const Icon(Icons.add_a_photo),
                  label: const Text('Add Photo'),
                ),
              ],
            ),
            const SizedBox(height: 8),
            if (widget.task.imageUrls.isEmpty)
              const Text('No photos attached')
            else
              SizedBox(
                height: 110,
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
                          ClipRRect(
                            borderRadius: BorderRadius.circular(8),
                            child: Image.network(url, height: 110, width: 140, fit: BoxFit.cover),
                          ),
                          Positioned(
                            right: 0,
                            child: Column(
                              children: [
                                IconButton(
                                  icon: const Icon(Icons.delete, color: Colors.red),
                                  onPressed: _saving ? null : () => _deleteImage(imageId),
                                ),
                                IconButton(
                                  icon: const Icon(Icons.refresh),
                                  onPressed: _saving ? null : () => _replaceImage(imageId),
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
          ],
        ),
      ),
    );
  }

  Widget _metaAndHistoryCard() {
    return Card(
      margin: const EdgeInsets.only(bottom: 24),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: ExpansionTile(
        leading: const Icon(Icons.info_outline),
        title: const Text('Meta & History'),
        childrenPadding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
        children: [
          // meta
          Align(
            alignment: Alignment.centerLeft,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Created by: ${widget.task.createdBy ?? "unknown"}'),
                Text('Modified by: ${widget.task.modifiedBy ?? widget.task.createdBy ?? "n/a"}'),
                const SizedBox(height: 12),
                const Text('History:', style: TextStyle(fontWeight: FontWeight.bold)),
              ],
            ),
          ),
          const SizedBox(height: 8),
          if (widget.task.history.isEmpty)
            const Align(
              alignment: Alignment.centerLeft,
              child: Text('No history available'),
            )
          else
            ...widget.task.history.map((h) => Padding(
                  padding: const EdgeInsets.only(bottom: 6),
                  child: Align(
                    alignment: Alignment.centerLeft,
                    child: Text('• $h'),
                  ),
                )),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }
    if (_error != null && _properties.isEmpty) {
      return Scaffold(
        appBar: AppBar(title: const Text('Edit Task')),
        body: Center(child: Text(_error!)),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('Edit Task'),
        actions: [
          TextButton.icon(
            onPressed: _saving ? null : _save,
            icon: const Icon(Icons.save),
            label: const Text('Save'),
            style: TextButton.styleFrom(
              foregroundColor: Theme.of(context).colorScheme.onPrimary,
            ),
          ),
        ],
      ),
      body: AbsorbPointer(
        absorbing: _saving,
        child: RefreshIndicator(
          onRefresh: _loadDropdowns,
          child: Form(
            key: _formKey,
            child: ListView(
              padding: const EdgeInsets.all(16),
              children: [
                _summaryCard(),
                _coreFormCard(),
                _notificationsInfoCard(), // read-only for context
                _photosCard(),
                _metaAndHistoryCard(),
                const SizedBox(height: 8),
                if (_error != null)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 8.0),
                    child: Text(_error!, style: const TextStyle(color: Colors.red)),
                  ),
                if (_saving)
                  const Center(child: Padding(
                    padding: EdgeInsets.only(top: 12),
                    child: CircularProgressIndicator(),
                  ))
                else
                  ElevatedButton.icon(
                    onPressed: _save,
                    icon: const Icon(Icons.save),
                    label: const Text('Save Changes'),
                  ),
              ],
            ),
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

  Color _statusColor(String status) {
    switch (status) {
      case 'pending':     return Colors.orange.shade100;
      case 'in-progress': return Colors.blue.shade100;
      case 'completed':   return Colors.green.shade100;
      case 'canceled':    return Colors.red.shade100;
      default:            return Colors.grey.shade200;
    }
  }
}