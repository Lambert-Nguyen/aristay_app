import 'dart:io';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:intl/intl.dart';
import '../models/task.dart';
import '../services/api_service.dart';

class TaskDetailScreen extends StatefulWidget {
  final Task? initialTask;          // when coming from list / edit
  final int?  taskId;               // when coming from push-notification

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

  @override
  void initState() {
    super.initState();
    if (widget.initialTask != null) {
      _task = widget.initialTask!;
      _refresh();                      // still refresh for freshness
    } else {
      // build a very small placeholder while we fetch the real record
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
      _refresh();                      // fetch from API
    }
  }

  Future<void> _refresh() async {
    setState(() => _loading = true);
    try {
      final updated = await ApiService().fetchTask(_task.id);
      setState(() { _task = updated; });
    } catch (e) {
      debugPrint('Failed to refresh task: $e');
    } finally {
      setState(() => _loading = false);
    }
  }

  String _formatLocal(DateTime utcDt) {
    final local = utcDt.toLocal();
    final fmt = DateFormat('yyyy-MM-dd HH:mm:ss');
    return '${fmt.format(local)} ${local.timeZoneName}';
  }

  void _openImage(String url) {
    Navigator.of(context).push(MaterialPageRoute(
      builder: (_) => Scaffold(
        backgroundColor: Colors.black,
        appBar: AppBar(backgroundColor: Colors.black),
        body: LayoutBuilder(
          builder: (context, constraints) {
            return InteractiveViewer(
              // Constrain to the full available space
              constrained: true,           
              // Allow a little extra for panning when zoomed
              boundaryMargin: const EdgeInsets.all(80),
              minScale: 1.0,
              maxScale: 4.0,
              child: SizedBox(
                width: constraints.maxWidth,
                height: constraints.maxHeight,
                child: Image.network(
                  url,
                  fit: BoxFit.contain,    // scale to fit entire area
                ),
              ),
            );
          },
        ),
      ),
    ));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Task Details'),
        actions: [
          // 🔕 mute / un-mute
          IconButton(
            tooltip: _task.isMuted ? 'Un-mute' : 'Mute',
            icon: Icon(_task.isMuted ? Icons.notifications_off : Icons.notifications),
            onPressed: () async {
              final old = _task.isMuted;
              setState(() => _task = _task.copyWith(isMuted: !old));

              bool ok = false;
              try {
                ok = old
                    ? await ApiService().unmuteTask(_task.id)
                    : await ApiService().muteTask  (_task.id);
              } catch (_) {
                ok = false;
              }

              if (!ok && mounted) {
                setState(() => _task = _task.copyWith(isMuted: old)); // rollback
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(content: Text('Failed to ${old ? "un-mute" : "mute"} task')),
                );
              }
            },
          ),
          IconButton(icon: const Icon(Icons.refresh), onPressed: _refresh),
          IconButton(
            icon: const Icon(Icons.edit),
            onPressed: () async {
              final result = await Navigator.pushNamed(context, '/edit-task', arguments: _task);
              if (result == true) await _refresh();
            },
          ),
          IconButton(
            icon: const Icon(Icons.delete),
            onPressed: () async {
              final ok = await ApiService().deleteTask(_task.id);
              if (ok) Navigator.popUntil(context, ModalRoute.withName('/tasks'));
              else ScaffoldMessenger.of(context)
                  .showSnackBar(const SnackBar(content: Text('Delete failed')));
            },
          ),
          IconButton(
            icon: const Icon(Icons.photo_camera),
            onPressed: () async {
              final img = await ImagePicker().pickImage(source: ImageSource.gallery);
              if (img == null) return;
              setState(() => _loading = true);
              await ApiService().uploadTaskImage(_task.id, File(img.path));
              await _refresh();
            },
          ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : Padding(
              padding: const EdgeInsets.all(16),
              child: ListView(
                children: [
                  Text('Task Type: ${_task.taskType}', style: const TextStyle(fontSize: 18)),
                  const SizedBox(height: 8),
                  Text('Title: ${_task.title}', style: const TextStyle(fontSize: 18)),
                  const SizedBox(height: 8),
                  Text('Description: ${_task.description}', style: const TextStyle(fontSize: 16)),
                  const Divider(height: 32),
                  Text('Property: ${_task.propertyName}', style: const TextStyle(fontSize: 16)),
                  const SizedBox(height: 8),
                  Text('Status: ${_task.status}', style: const TextStyle(fontSize: 16)),
                  const Divider(height: 32),
                  Text('Created At (Local): ${_formatLocal(_task.createdAt)}',
                      style: const TextStyle(fontSize: 14)),
                  Text('Modified At (Local): ${_formatLocal(_task.modifiedAt)}',
                      style: const TextStyle(fontSize: 14)),
                  const Divider(height: 32),
                  Text('Created by: ${_task.createdBy ?? "unknown"}',
                      style: const TextStyle(fontSize: 16)),
                  const SizedBox(height: 8),
                  Text('Assigned to: ${_task.assignedToUsername ?? "Not assigned"}',
                      style: const TextStyle(fontSize: 16)),
                  const SizedBox(height: 8),
                  Text('Modified by: ${_task.modifiedBy ?? _task.createdBy ?? "n/a"}',
                      style: const TextStyle(fontSize: 16)),
                  const Divider(height: 32),
                  const Text('History:',
                      style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                  if (_task.history.isEmpty)
                    const Text('No history available', style: TextStyle(fontSize: 16))
                  else
                    ..._task.history.map((h) => Padding(
                          padding: const EdgeInsets.symmetric(vertical: 4),
                          child: Text('• $h', style: const TextStyle(fontSize: 16)),
                        )),
                  const Divider(height: 32),
                  const Text('Photos:', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 8),
                  if (_task.imageUrls.isEmpty)
                    const Text('No photos attached')
                  else
                    SizedBox(
                      height: 100,
                      child: ListView.builder(
                        scrollDirection: Axis.horizontal,
                        itemCount: _task.imageUrls.length,
                        itemBuilder: (_, i) {
                          final url = _task.imageUrls[i];
                          return GestureDetector(
                            onTap: () => _openImage(url),
                            child: Padding(
                              padding: const EdgeInsets.only(right: 8),
                              child: Image.network(
                                url,
                                height: 100,
                                fit: BoxFit.cover,
                              ),
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
}