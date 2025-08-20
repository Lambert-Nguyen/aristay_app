// lib/screens/task_detail_screen.dart
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:intl/intl.dart';
import '../models/task.dart';
import '../services/api_service.dart';

class TaskDetailScreen extends StatefulWidget {
  final Task? initialTask;
  final int?  taskId;

  const TaskDetailScreen({
    Key? key,
    this.initialTask,
    this.taskId,
  }) : assert(initialTask != null || taskId != null,
        'Either initialTask or taskId must be supplied'),
       super(key: key);

  @override
  State<TaskDetailScreen> createState() => _TaskDetailScreenState();
}

class _TaskDetailScreenState extends State<TaskDetailScreen> {
  late Task _task;
  bool _loading = false;
  bool _dirty   = false;

  final _fmt = DateFormat('yyyy-MM-dd HH:mm:ss');

  @override
  void initState() {
    super.initState();
    if (widget.initialTask != null) {
      _task = widget.initialTask!;
      _refresh();
    } else {
      _task = Task(
        id:          widget.taskId!,
        propertyId:  0,
        propertyName:'Loading…',
        taskType:    '',
        title:       'Loading…',
        description: '',
        status:      '',
        createdAt:   DateTime.now().toUtc(),
        modifiedAt:  DateTime.now().toUtc(),
      );
      _refresh();
    }
  }

  Future<void> _refresh() async {
    setState(() => _loading = true);
    try {
      final updated = await ApiService().fetchTask(_task.id);
      setState(() => _task = updated);
    } catch (e) {
      debugPrint('Failed to refresh task: $e');
    } finally {
      setState(() => _loading = false);
    }
  }

  String _formatLocal(DateTime utcDt) {
    final local = utcDt.toLocal();
    return '${_fmt.format(local)} ${local.timeZoneName}';
  }

  Future<void> _toggleMute(bool next) async {
    final old = _task.isMuted;
    setState(() => _task = _task.copyWith(isMuted: next));
    bool ok;
    try {
      ok = next
        ? await ApiService().muteTask(_task.id)
        : await ApiService().unmuteTask(_task.id);
    } catch (_) {
      ok = false;
    }
    if (!ok && mounted) {
      setState(() => _task = _task.copyWith(isMuted: old)); // rollback
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Failed to ${next ? "mute" : "un-mute"} task')),
      );
    } else if (ok) {
      _dirty = true;
    }
  }

  Future<void> _attachPhoto() async {
    final img = await ImagePicker().pickImage(source: ImageSource.gallery);
    if (img == null) return;
    setState(() => _loading = true);
    try {
      await ApiService().uploadTaskImage(_task.id, File(img.path));
      await _refresh();
      _dirty = true;
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _confirmDelete() async {
    final yes = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Delete task?'),
        content: const Text('This cannot be undone.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancel')),
          TextButton(onPressed: () => Navigator.pop(context, true),  child: const Text('Delete')),
        ],
      ),
    );
    if (yes != true) return;

    final ok = await ApiService().deleteTask(_task.id);
    if (!mounted) return;
    if (ok) {
      Navigator.popUntil(context, ModalRoute.withName('/tasks'));
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Delete failed')),
      );
    }
  }

  void _openImage(String url) {
    Navigator.of(context).push(MaterialPageRoute(
      builder: (_) => Scaffold(
        backgroundColor: Colors.black,
        appBar: AppBar(backgroundColor: Colors.black),
        body: Center(
          child: InteractiveViewer(
            minScale: 1.0,
            maxScale: 4.0,
            child: Image.network(url, fit: BoxFit.contain),
          ),
        ),
      ),
    ));
  }

  Widget _headerCard() {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Title + status chip
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: Text(_task.title,
                    style: const TextStyle(
                      fontSize: 20, fontWeight: FontWeight.w700)),
                ),
                Chip(
                  label: Text(_task.status.replaceAll('-', ' ')),
                  backgroundColor: _statusColor(_task.status),
                )
              ],
            ),
            const SizedBox(height: 8),
            // Property & type
            Row(
              children: [
                const Icon(Icons.home_outlined, size: 18),
                const SizedBox(width: 6),
                Expanded(child: Text(_task.propertyName)),
                const SizedBox(width: 8),
                const Icon(Icons.build_outlined, size: 18),
                const SizedBox(width: 6),
                Text(_task.taskType),
              ],
            ),
            const SizedBox(height: 8),
            // Assignee
            Row(
              children: [
                const Icon(Icons.person_outline, size: 18),
                const SizedBox(width: 6),
                Expanded(child: Text(_task.assignedToUsername ?? 'Not assigned')),
              ],
            ),
            const Divider(height: 24),
            // Dates
            Text('Created:  ${_formatLocal(_task.createdAt)}',
                style: const TextStyle(fontSize: 12, color: Colors.grey)),
            Text('Modified: ${_formatLocal(_task.modifiedAt)}',
                style: const TextStyle(fontSize: 12, color: Colors.grey)),
          ],
        ),
      ),
    );
  }

  Widget _descriptionCard() {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Text(
          _task.description.isEmpty ? 'No description' : _task.description,
          style: const TextStyle(fontSize: 16),
        ),
      ),
    );
  }

  Widget _notificationsCard() {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: SwitchListTile(
        dense: false,
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
        title: const Text('Mute notifications for this task'),
        subtitle: Text(_task.isMuted ? 'Muted for you' : 'Enabled for you'),
        secondary: Icon(_task.isMuted ? Icons.notifications_off : Icons.notifications),
        value: _task.isMuted,
        onChanged: (v) => _toggleMute(v),
      ),
    );
  }

  Widget _photosCard() {
    if (_task.imageUrls.isEmpty) {
      return Card(
        margin: const EdgeInsets.only(bottom: 12),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        child: const ListTile(
          leading: Icon(Icons.photo_outlined),
          title: Text('No photos attached'),
        ),
      );
    }
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 8),
        child: SizedBox(
          height: 110,
          child: ListView.separated(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 12),
            itemCount: _task.imageUrls.length,
            separatorBuilder: (_, __) => const SizedBox(width: 8),
            itemBuilder: (_, i) {
              final url = _task.imageUrls[i];
              return GestureDetector(
                onTap: () => _openImage(url),
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(8),
                  child: Image.network(url, height: 110, width: 140, fit: BoxFit.cover),
                ),
              );
            },
          ),
        ),
      ),
    );
  }

  Widget _historyCard() {
    return Card(
      margin: const EdgeInsets.only(bottom: 24),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: ExpansionTile(
        leading: const Icon(Icons.timelapse),
        title: const Text('History'),
        childrenPadding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
        children: _task.history.isEmpty
            ? [const Align(
                alignment: Alignment.centerLeft,
                child: Padding(
                  padding: EdgeInsets.only(bottom: 12),
                  child: Text('No history available'),
                ),
              )]
            : _task.history.map((h) => Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: Align(
                    alignment: Alignment.centerLeft,
                    child: Text('• $h'),
                  ),
                )).toList(),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return PopScope(
      canPop: false,
      onPopInvokedWithResult: (didPop, _) {
        if (didPop) return;
        Navigator.pop(context, _dirty ? _task : null);
      },
      child: Scaffold(
        appBar: AppBar(
          title: const Text('Task Details'),
          leading: IconButton(
            icon: const Icon(Icons.arrow_back),
            onPressed: () => Navigator.pop(context, _dirty ? _task : null),
          ),
          actions: [
            PopupMenuButton<String>(
              onSelected: (val) async {
                switch (val) {
                  case 'edit':
                    final result = await Navigator.pushNamed(context, '/edit-task', arguments: _task);
                    if (result == true) {
                      await _refresh();
                      _dirty = true;
                    }
                    break;
                  case 'photo':
                    await _attachPhoto();
                    break;
                  case 'refresh':
                    await _refresh();
                    break;
                  case 'delete':
                    await _confirmDelete();
                    break;
                }
              },
              itemBuilder: (_) => [
                const PopupMenuItem(value: 'edit',    child: ListTile(leading: Icon(Icons.edit),          title: Text('Edit'))),
                const PopupMenuItem(value: 'photo',   child: ListTile(leading: Icon(Icons.photo_camera),   title: Text('Add photo'))),
                const PopupMenuItem(value: 'refresh', child: ListTile(leading: Icon(Icons.refresh),        title: Text('Refresh'))),
                PopupMenuItem(
                  value: 'delete',
                  child: ListTile(
                    leading: const Icon(Icons.delete, color: Colors.red),
                    title: const Text('Delete', style: TextStyle(color: Colors.red)),
                  ),
                ),
              ],
            ),
          ],
        ),
        body: _loading
            ? const Center(child: CircularProgressIndicator())
            : RefreshIndicator(
                onRefresh: _refresh,
                child: ListView(
                  padding: const EdgeInsets.all(16),
                  children: [
                    _headerCard(),
                    _descriptionCard(),
                    _notificationsCard(), // ← mute/unmute lives here now
                    _photosCard(),
                    _historyCard(),
                  ],
                ),
              ),
      ),
    );
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