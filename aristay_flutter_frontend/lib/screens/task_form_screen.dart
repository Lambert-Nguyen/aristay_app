import 'dart:io';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import '../models/property.dart';
import '../models/user.dart';
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
  final _imagePicker = ImagePicker();

  // Data
  List<Property> _properties = [];
  bool _propertiesLoading = true;
  Property? _selectedProperty;
  DateTime? _dueLocal;

  // Assignee data (lazy loaded)
  List<User> _users = [];
  bool _usersLoading = false;
  String? _usersError;
  User? _assignee;

  // Form fields
  String _taskType = 'cleaning';
  String _status = 'pending';
  File? _pickedImage;

  // UI state
  bool _submitting = false;
  String? _pageError; // top-level error (non-field)
  Map<String, String> _fieldErrors = {}; // server-side field errors

  final GlobalKey<FormFieldState<Property?>> _propertyFieldKey =
      GlobalKey<FormFieldState<Property?>>();
  final GlobalKey<FormFieldState<User?>> _assigneeFieldKey =
      GlobalKey<FormFieldState<User?>>();

  @override
  void initState() {
    super.initState();
    _loadProperties();
  }

  Future<void> _loadProperties() async {
    setState(() {
      _propertiesLoading = true;
      _pageError = null;
    });
    try {
      final list = await ApiService().fetchProperties();
      setState(() => _properties = list);
    } catch (_) {
      setState(() => _pageError = 'Failed to load properties');
    } finally {
      setState(() => _propertiesLoading = false);
    }
  }

  Future<void> _ensureUsersLoaded() async {
    if (_usersLoading || _users.isNotEmpty) return;
    setState(() {
      _usersLoading = true;
      _usersError = null;
    });
    try {
      final res = await ApiService().fetchUsers();
      final results = (res['results'] as List<User>);
      setState(() => _users = results);
    } catch (e) {
      setState(() => _usersError = 'Failed to load users');
    } finally {
      setState(() => _usersLoading = false);
    }
  }

  Future<void> _pickImageFrom(ImageSource source) async {
    final picked = await _imagePicker.pickImage(source: source, imageQuality: 85);
    if (picked != null) setState(() => _pickedImage = File(picked.path));
  }

  void _showImagePickerSheet() {
    showModalBottomSheet<void>(
      context: context,
      showDragHandle: true,
      builder: (_) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(
              leading: const Icon(Icons.photo_camera_outlined),
              title: const Text('Take photo'),
              onTap: () {
                Navigator.pop(context);
                _pickImageFrom(ImageSource.camera);
              },
            ),
            ListTile(
              leading: const Icon(Icons.photo_library_outlined),
              title: const Text('Choose from library'),
              onTap: () {
                Navigator.pop(context);
                _pickImageFrom(ImageSource.gallery);
              },
            ),
            if (_pickedImage != null)
              ListTile(
                leading: const Icon(Icons.delete_outline, color: Colors.redAccent),
                title: const Text('Remove photo'),
                onTap: () {
                  setState(() => _pickedImage = null);
                  Navigator.pop(context);
                },
              ),
          ],
        ),
      ),
    );
  }

  Future<void> _pickDueDate() async {
    final now = DateTime.now();
    final date = await showDatePicker(
      context: context,
      firstDate: DateTime(now.year - 1),
      lastDate: DateTime(now.year + 3),
      initialDate: _dueLocal ?? now,
    );
    if (date == null) return;
    final time = await showTimePicker(
      context: context,
      initialTime: _dueLocal != null
          ? TimeOfDay.fromDateTime(_dueLocal!)
          : TimeOfDay.now(),
    );
    if (time == null) return;
    setState(() {
      _dueLocal = DateTime(date.year, date.month, date.day, time.hour, time.minute);
    });
  }

  Future<void> _openPropertyPicker() async {
    final picked = await showModalBottomSheet<Property>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (context) {
      String query = '';
      return SafeArea(
        child: StatefulBuilder(
          builder: (context, setModalState) {
            final filtered = _properties.where((p) {
              if (query.isEmpty) return true;
              final q = query.toLowerCase();
              return p.name.toLowerCase().contains(q);
            }).toList();

            return Padding(
              padding: EdgeInsets.only(
                bottom: MediaQuery.of(context).viewInsets.bottom,
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const _SheetHeader(title: 'Select property'),
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                    child: TextField(
                      autofocus: true,
                      decoration: const InputDecoration(
                        labelText: 'Search properties',
                        prefixIcon: Icon(Icons.search),
                      ),
                      onChanged: (v) => setModalState(() => query = v),
                    ),
                  ),
                  Flexible(
                    child: ListView.separated(
                      shrinkWrap: true,
                      itemCount: filtered.length,
                      separatorBuilder: (_, __) => const Divider(height: 1),
                      itemBuilder: (_, i) {
                        final p = filtered[i];
                        return ListTile(
                          title: Text(p.name),
                          onTap: () => Navigator.pop(context, p),
                        );
                      },
                    ),
                  ),
                ],
              ),
            );
          },
        ),
      );
    },
    );

    if (picked != null) {
      setState(() => _selectedProperty = picked);
      _propertyFieldKey.currentState?.didChange(picked);
    }
  }

  Future<void> _openAssigneePicker() async {
    await _ensureUsersLoaded();

    final picked = await showModalBottomSheet<User>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (context) {
        String query = '';
        return SafeArea(
          child: StatefulBuilder(
            builder: (context, setModalState) {
              if (_usersLoading) {
                return const Padding(
                  padding: EdgeInsets.all(24),
                  child: Center(child: CircularProgressIndicator()),
                );
              }
              if (_usersError != null) {
                return Padding(
                  padding: const EdgeInsets.all(24),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const _SheetHeader(title: 'Select assignee'),
                      Text(_usersError!, style: const TextStyle(color: Colors.red)),
                      const SizedBox(height: 12),
                      FilledButton(
                        onPressed: () async {
                          setModalState(() {
                            _usersLoading = true;
                            _usersError = null;
                          });
                          try {
                            final res = await ApiService().fetchUsers();
                            final results = (res['results'] as List<User>);
                            setModalState(() => _users = results);
                          } catch (e) {
                            setModalState(() => _usersError = 'Failed to load users');
                          } finally {
                            setModalState(() => _usersLoading = false);
                          }
                        },
                        child: const Text('Retry'),
                      ),
                    ],
                  ),
                );
              }

              final filtered = _users.where((u) {
                if (query.isEmpty) return true;
                final q = query.toLowerCase();
                final parts = <String>[
                  u.username,
                  (u.firstName ?? ''),
                  (u.lastName ?? ''),
                  (u.email ?? ''),
                ].join(' ').toLowerCase();
                return parts.contains(q);
              }).toList();

              String label(User u) {
                final fn = (u.firstName ?? '').trim();
                final ln = (u.lastName ?? '').trim();
                final full = ('$fn $ln').trim();
                return full.isNotEmpty ? '$full (@${u.username})' : u.username;
              }

              return Padding(
                padding: EdgeInsets.only(
                  bottom: MediaQuery.of(context).viewInsets.bottom,
                ),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const _SheetHeader(title: 'Select assignee'),
                    Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                      child: TextField(
                        autofocus: true,
                        decoration: const InputDecoration(
                          labelText: 'Search users',
                          prefixIcon: Icon(Icons.search),
                        ),
                        onChanged: (v) => setModalState(() => query = v),
                      ),
                    ),
                    Flexible(
                      child: ListView.separated(
                        shrinkWrap: true,
                        itemCount: filtered.length,
                        separatorBuilder: (_, __) => const Divider(height: 1),
                        itemBuilder: (_, i) {
                          final u = filtered[i];
                          return ListTile(
                            leading: CircleAvatar(
                              radius: 16,
                              child: Text(
                                (u.firstName?.isNotEmpty == true
                                        ? u.firstName![0]
                                        : (u.username.isNotEmpty ? u.username[0] : '?'))
                                    .toUpperCase(),
                              ),
                            ),
                            title: Text(label(u)),
                            subtitle: (u.email?.isNotEmpty ?? false) ? Text(u.email!) : null,
                            onTap: () => Navigator.pop(context, u),
                          );
                        },
                      ),
                    ),
                  ],
                ),
              );
            },
          ),
        );
      },
    );

    if (picked != null) {
      setState(() => _assignee = picked);
      _assigneeFieldKey.currentState?.didChange(picked);
    }
  }

  String _formatDueDate(BuildContext context) {
    final l = MaterialLocalizations.of(context);
    final d = _dueLocal!;
    return '${l.formatFullDate(d)} · ${l.formatTimeOfDay(TimeOfDay.fromDateTime(d), alwaysUse24HourFormat: false)}';
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    if (_selectedProperty == null) {
      _propertyFieldKey.currentState?.validate();
      return;
    }

    setState(() {
      _submitting = true;
      _pageError = null;
      _fieldErrors.clear();
    });

    try {
      final payload = {
        'property': _selectedProperty!.id,
        'task_type': _taskType,
        'title': _titleCtrl.text.trim(),
        'description': _descCtrl.text.trim(),
        'status': _status,
        if (_assignee != null) 'assigned_to': _assignee!.id,
        if (_dueLocal != null) 'due_date': _dueLocal!.toUtc().toIso8601String(),
      };
      final created = await ApiService().createTask(payload);

      final int newTaskId = created['id'] as int;
      if (_pickedImage != null) {
        await ApiService().uploadTaskImage(newTaskId, _pickedImage!);
      }

      if (!mounted) return;
      Navigator.pop(context, true);
    } on ValidationException catch (ve) {
      setState(() => _fieldErrors = ve.errors);
      _formKey.currentState!.validate();
      _propertyFieldKey.currentState?.validate();
      _assigneeFieldKey.currentState?.validate();
    } catch (e) {
      setState(() => _pageError = e.toString());
    } finally {
      setState(() => _submitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    final body = _propertiesLoading
        ? const Center(child: CircularProgressIndicator())
        : _properties.isEmpty
            ? _EmptyState(onRetry: _loadProperties)
            : Form(
                key: _formKey,
                autovalidateMode: AutovalidateMode.onUserInteraction,
                child: ListView(
                  padding: const EdgeInsets.all(16),
                  children: [
                    if (_pageError != null)
                      Card(
                        margin: const EdgeInsets.only(bottom: 12),
                        color: theme.colorScheme.errorContainer,
                        child: Padding(
                          padding: const EdgeInsets.all(12),
                          child: Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Icon(Icons.error_outline,
                                  color: theme.colorScheme.onErrorContainer),
                              const SizedBox(width: 8),
                              Expanded(
                                child: Text(
                                  _pageError!,
                                  style: TextStyle(
                                    color: theme.colorScheme.onErrorContainer,
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),

                    // Property
                    _CardSection(
                      icon: Icons.apartment_outlined,
                      title: 'Property',
                      child: FormField<Property?>(
                        key: _propertyFieldKey,
                        validator: (_) {
                          if (_selectedProperty == null) return 'Pick one';
                          return _fieldErrors['property'];
                        },
                        builder: (state) {
                          return ListTile(
                            contentPadding: EdgeInsets.zero,
                            leading: CircleAvatar(
                              radius: 16,
                              child: Text(
                                (_selectedProperty?.name ?? 'P')
                                    .substring(0, 1)
                                    .toUpperCase(),
                              ),
                            ),
                            title: Text(
                              _selectedProperty?.name ?? 'Tap to choose',
                              style: _selectedProperty == null
                                  ? theme.textTheme.bodyLarge
                                      ?.copyWith(color: theme.hintColor)
                                  : theme.textTheme.bodyLarge,
                            ),
                            trailing: IconButton(
                              tooltip: 'Choose property',
                              icon: const Icon(Icons.chevron_right),
                              onPressed: _openPropertyPicker,
                            ),
                            onTap: _openPropertyPicker,
                            subtitle: state.errorText == null
                                ? null
                                : Padding(
                                    padding: const EdgeInsets.only(top: 6),
                                    child: Text(
                                      state.errorText!,
                                      style: TextStyle(
                                        color: theme.colorScheme.error,
                                        fontSize: 12,
                                      ),
                                    ),
                                  ),
                          );
                        },
                      ),
                    ),

                    // Task Type
                    _CardSection(
                      icon: Icons.category_outlined,
                      title: 'Task type',
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          SegmentedButton<String>(
                            segments: const [
                              ButtonSegment(
                                  value: 'cleaning',
                                  label: Text('Cleaning'),
                                  icon: Icon(Icons.cleaning_services)),
                              ButtonSegment(
                                  value: 'maintenance',
                                  label: Text('Maintenance'),
                                  icon: Icon(Icons.build_outlined)),
                            ],
                            selected: {_taskType},
                            onSelectionChanged: (s) =>
                                setState(() => _taskType = s.first),
                          ),
                          if (_fieldErrors['task_type'] != null)
                            Padding(
                              padding: const EdgeInsets.only(top: 8),
                              child: Text(
                                _fieldErrors['task_type']!,
                                style: TextStyle(
                                  color: theme.colorScheme.error,
                                  fontSize: 12,
                                ),
                              ),
                            ),
                        ],
                      ),
                    ),

                    // Details
                    _CardSection(
                      icon: Icons.description_outlined,
                      title: 'Details',
                      child: Column(
                        children: [
                          TextFormField(
                            controller: _titleCtrl,
                            decoration: InputDecoration(
                              labelText: 'Title',
                              errorText: _fieldErrors['title'],
                            ),
                            textInputAction: TextInputAction.next,
                            validator: (v) =>
                                (v == null || v.trim().isEmpty)
                                    ? 'Required'
                                    : null,
                          ),
                          const SizedBox(height: 12),
                          TextFormField(
                            controller: _descCtrl,
                            decoration: InputDecoration(
                              labelText: 'Description',
                              helperText: 'Optional — add context for assignees',
                              errorText: _fieldErrors['description'],
                            ),
                            maxLines: 4,
                          ),
                        ],
                      ),
                    ),

                    // Assignee (optional)
                    _CardSection(
                      icon: Icons.person_add_outlined,
                      title: 'Assignee (optional)',
                      child: FormField<User?>(
                        key: _assigneeFieldKey,
                        validator: (_) => _fieldErrors['assigned_to'],
                        builder: (state) {
                          String display(User u) {
                            final fn = (u.firstName ?? '').trim();
                            final ln = (u.lastName ?? '').trim();
                            final full = ('$fn $ln').trim();
                            return full.isNotEmpty ? '$full (@${u.username})' : u.username;
                          }

                          return ListTile(
                            contentPadding: EdgeInsets.zero,
                            leading: CircleAvatar(
                              radius: 16,
                              child: Text(
                                (_assignee == null
                                        ? 'A'
                                        : ( (_assignee!.firstName?.isNotEmpty ?? false)
                                            ? _assignee!.firstName![0]
                                            : _assignee!.username[0]))
                                    .toUpperCase(),
                              ),
                            ),
                            title: Text(
                              _assignee == null
                                  ? 'Tap to choose'
                                  : display(_assignee!),
                              style: _assignee == null
                                  ? theme.textTheme.bodyLarge
                                      ?.copyWith(color: theme.hintColor)
                                  : theme.textTheme.bodyLarge,
                            ),
                            trailing: Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                if (_assignee != null)
                                  IconButton(
                                    tooltip: 'Clear',
                                    icon: const Icon(Icons.clear),
                                    onPressed: () {
                                      setState(() => _assignee = null);
                                      _assigneeFieldKey.currentState?.didChange(null);
                                    },
                                  ),
                                IconButton(
                                  tooltip: 'Choose assignee',
                                  icon: const Icon(Icons.chevron_right),
                                  onPressed: _openAssigneePicker,
                                ),
                              ],
                            ),
                            onTap: _openAssigneePicker,
                            subtitle: state.errorText == null
                                ? null
                                : Padding(
                                    padding: const EdgeInsets.only(top: 6),
                                    child: Text(
                                      state.errorText!,
                                      style: TextStyle(
                                        color: theme.colorScheme.error,
                                        fontSize: 12,
                                      ),
                                    ),
                                  ),
                          );
                        },
                      ),
                    ),

                    // Status
                    _CardSection(
                      icon: Icons.flag_outlined,
                      title: 'Status',
                      child: _ResponsiveStatusPicker(
                        value: _status,
                        onChanged: (v) => setState(() => _status = v),
                        errorText: _fieldErrors['status'],
                      ),
                    ),

                    // Due date
                    _CardSection(
                      icon: Icons.event_outlined,
                      title: 'Due date (optional)',
                      child: Row(
                        children: [
                          Expanded(
                            child: FilledButton.tonalIcon(
                              onPressed: _submitting ? null : _pickDueDate,
                              icon: const Icon(Icons.event),
                              label: Text(
                                _dueLocal == null ? 'Set due date' : _formatDueDate(context),
                                overflow: TextOverflow.ellipsis, // prevent long text overflow
                                maxLines: 1,
                              ),
                            ),
                          ),
                          const SizedBox(width: 12),
                          if (_dueLocal != null)
                            TextButton.icon(
                              onPressed: _submitting ? null : () => setState(() => _dueLocal = null),
                              icon: const Icon(Icons.clear),
                              label: const Text('Clear'),
                            ),
                        ],
                      ),
                    ),

                    // Photo
                    _CardSection(
                      icon: Icons.photo_outlined,
                      title: 'Photo (optional)',
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              FilledButton.tonalIcon(
                                onPressed:
                                    _submitting ? null : _showImagePickerSheet,
                                icon: const Icon(Icons.photo),
                                label: Text(
                                    _pickedImage == null ? 'Attach photo' : 'Change photo'),
                              ),
                              const SizedBox(width: 12),
                              if (_pickedImage != null)
                                TextButton.icon(
                                  onPressed: _submitting
                                      ? null
                                      : () => setState(() => _pickedImage = null),
                                  icon: const Icon(Icons.delete_outline),
                                  label: const Text('Remove'),
                                ),
                            ],
                          ),
                          if (_pickedImage != null)
                            Padding(
                              padding: const EdgeInsets.only(top: 12),
                              child: ClipRRect(
                                borderRadius: BorderRadius.circular(12),
                                child: Image.file(
                                  _pickedImage!,
                                  height: 140,
                                  width: double.infinity,
                                  fit: BoxFit.cover,
                                ),
                              ),
                            ),
                        ],
                      ),
                    ),

                    const SizedBox(height: 88), // space for bottom bar
                  ],
                ),
              );

    return GestureDetector(
      onTap: () => FocusScope.of(context).unfocus(),
      child: Scaffold(
        appBar: AppBar(
          title: const Text('New Task'),
        ),
        body: SafeArea(child: body),
        bottomNavigationBar: SafeArea(
          top: false,
          child: Padding(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 16),
            child: SizedBox(
              width: double.infinity,
              child: FilledButton.icon(
                onPressed: _submitting ? null : _submit,
                icon: _submitting
                    ? const SizedBox(
                        width: 18,
                        height: 18,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.add_task),
                label: const Text('Create Task'),
              ),
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
}

class _CardSection extends StatelessWidget {
  const _CardSection({
    required this.icon,
    required this.title,
    required this.child,
  });

  final IconData icon;
  final String title;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      elevation: 0,
      surfaceTintColor: theme.colorScheme.surfaceTint,
      child: Padding(
        padding: const EdgeInsets.fromLTRB(16, 12, 16, 16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(children: [
              Icon(icon, size: 20, color: theme.colorScheme.primary),
              const SizedBox(width: 8),
              Text(
                title,
                style: theme.textTheme.titleSmall?.copyWith(
                  color: theme.colorScheme.onSurfaceVariant,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ]),
            const SizedBox(height: 12),
            child,
          ],
        ),
      ),
    );
  }
}

class _EmptyState extends StatelessWidget {
  const _EmptyState({required this.onRetry});
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.apartment_outlined, size: 48),
            const SizedBox(height: 12),
            const Text(
              'No properties found',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 8),
            const Text(
              'You need a property to attach the task to.',
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 16),
            FilledButton.icon(
              onPressed: onRetry,
              icon: const Icon(Icons.refresh),
              label: const Text('Retry'),
            ),
          ],
        ),
      ),
    );
  }
}

class _SheetHeader extends StatelessWidget {
  const _SheetHeader({required this.title});
  final String title;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.fromLTRB(4, 4, 4, 8),
      child: Row(
        children: [
          IconButton(
            icon: const Icon(Icons.arrow_back),
            onPressed: () => Navigator.pop(context),
          ),
          const SizedBox(width: 4),
          Text(
            title,
            style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600),
          ),
          const Spacer(),
        ],
      ),
    );
  }
}

class _ResponsiveStatusPicker extends StatelessWidget {
  const _ResponsiveStatusPicker({
    required this.value,
    required this.onChanged,
    this.errorText,
  });

  final String value;
  final ValueChanged<String> onChanged;
  final String? errorText;

  static const _options = [
    ('pending', 'Pending', Icons.pause_circle_outline),
    ('in-progress', 'In progress', Icons.play_circle_outline),
    ('completed', 'Completed', Icons.check_circle_outline),
    ('canceled', 'Canceled', Icons.cancel_outlined),
  ];

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (_, c) {
        final compact = c.maxWidth < 360; // break point for small phones
        final error = errorText == null
            ? null
            : Padding(
                padding: const EdgeInsets.only(top: 8),
                child: Text(
                  errorText!,
                  style: TextStyle(
                    color: Theme.of(context).colorScheme.error,
                    fontSize: 12,
                  ),
                ),
              );

        if (compact) {
          return Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: _options.map((o) {
                  final selected = value == o.$1;
                  return ChoiceChip(
                    avatar: Icon(o.$3, size: 18),
                    label: Text(o.$2),
                    selected: selected,
                    onSelected: (_) => onChanged(o.$1),
                  );
                }).toList(),
              ),
              if (error != null) error,
            ],
          );
        }

        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            SegmentedButton<String>(
              segments: _options
                  .map((o) => ButtonSegment(
                        value: o.$1,
                        label: Text(o.$2),
                        icon: Icon(o.$3),
                      ))
                  .toList(),
              selected: {value},
              onSelectionChanged: (s) => onChanged(s.first),
            ),
            if (error != null) error,
          ],
        );
      },
    );
  }
}