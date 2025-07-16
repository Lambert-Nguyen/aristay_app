import 'package:flutter/material.dart';
import '../models/property.dart';
import '../models/user.dart';

class TaskAdvancedFilterSheet extends StatefulWidget {
  final List<Property> properties;
  final List<User> assignees;
  final int? selectedProperty;
  final int? selectedAssignee;
  final DateTime? dateFrom;
  final DateTime? dateTo;
  final void Function({
    int? property,
    int? assignedTo,
    DateTime? dateFrom,
    DateTime? dateTo,
  }) onApply;

  const TaskAdvancedFilterSheet({
    Key? key,
    required this.properties,
    required this.assignees,
    this.selectedProperty,
    this.selectedAssignee,
    this.dateFrom,
    this.dateTo,
    required this.onApply,
  }) : super(key: key);

  @override
  State<TaskAdvancedFilterSheet> createState() =>
      _TaskAdvancedFilterSheetState();
}

class _TaskAdvancedFilterSheetState extends State<TaskAdvancedFilterSheet> {
  int? _property;
  int? _assignee;
  DateTime? _from;
  DateTime? _to;

  @override
  void initState() {
    super.initState();
    _property = widget.selectedProperty;
    _assignee = widget.selectedAssignee;
    _from     = widget.dateFrom;
    _to       = widget.dateTo;
  }

  Future<void> _pickFrom() async {
    final picked = await showDatePicker(
      context: context,
      initialDate: _from ?? DateTime.now(),
      firstDate: DateTime(2000),
      lastDate: DateTime.now().add(const Duration(days: 365)),
    );
    if (picked != null) setState(() => _from = picked);
  }

  Future<void> _pickTo() async {
    final picked = await showDatePicker(
      context: context,
      initialDate: _to ?? DateTime.now(),
      firstDate: DateTime(2000),
      lastDate: DateTime.now().add(const Duration(days: 365)),
    );
    if (picked != null) setState(() => _to = picked);
  }

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // draggable handle
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 8),
            child: Container(
              width: 40, height: 4,
              decoration: BoxDecoration(
                color: Colors.grey[400],
                borderRadius: BorderRadius.circular(2),
              ),
            ),
          ),

          // Property
          ListTile(
            leading: const Icon(Icons.home_outlined),
            title: const Text('Property'),
            trailing: DropdownButton<int?>(
              value: _property,
              items: [
                const DropdownMenuItem(value: null, child: Text('All')),
                ...widget.properties.map((p) =>
                  DropdownMenuItem(value: p.id, child: Text(p.name))
                )
              ],
              onChanged: (v) => setState(() => _property = v),
            ),
          ),

          // Assignee
          ListTile(
            leading: const Icon(Icons.person_outline),
            title: const Text('Assigned To'),
            trailing: DropdownButton<int?>(
              value: _assignee,
              items: [
                const DropdownMenuItem(value: null, child: Text('All')),
                ...widget.assignees.map((u) =>
                  DropdownMenuItem(value: u.id, child: Text(u.username))
                )
              ],
              onChanged: (v) => setState(() => _assignee = v),
            ),
          ),

          // Date From
          ListTile(
            leading: const Icon(Icons.date_range),
            title: const Text('Date From'),
            trailing: TextButton(
              onPressed: _pickFrom,
              child: Text(
                _from == null
                  ? 'Any'
                  : "${_from!.year}/${_from!.month}/${_from!.day}"
              ),
            ),
          ),

          // Date To
          ListTile(
            leading: const Icon(Icons.date_range),
            title: const Text('Date To'),
            trailing: TextButton(
              onPressed: _pickTo,
              child: Text(
                _to == null
                  ? 'Any'
                  : "${_to!.year}/${_to!.month}/${_to!.day}"
              ),
            ),
          ),

          const SizedBox(height: 8),

          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: ElevatedButton(
              onPressed: () {
                Navigator.pop(context);
                widget.onApply(
                  property:   _property,
                  assignedTo: _assignee,
                  dateFrom:   _from,
                  dateTo:     _to,
                );
              },
              child: const Text('Apply Filters'),
            ),
          ),

          const SizedBox(height: 16),
        ],
      ),
    );
  }
}