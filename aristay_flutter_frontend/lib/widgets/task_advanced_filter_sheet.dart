import 'package:flutter/material.dart';
import '../models/property.dart';
import '../models/user.dart';

class TaskAdvancedFilterSheet extends StatefulWidget {
  final bool? overdue;

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
    bool? overdue,
  }) onApply;

  const TaskAdvancedFilterSheet({
    Key? key,
    required this.properties,
    required this.assignees,
    this.selectedProperty,
    this.selectedAssignee,
    this.dateFrom,
    this.dateTo,
    this.overdue,
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
  bool _overdue = false;

  @override
  void initState() {
    super.initState();
    _property = widget.selectedProperty;
    _assignee = widget.selectedAssignee;
    _from = widget.dateFrom;
    _to = widget.dateTo;
    _overdue = widget.overdue ?? false;
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

  void _resetLocal() {
    setState(() {
      _property = null;
      _assignee = null;
      _from = null;
      _to = null;
      _overdue = false;
    });
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
              width: 40,
              height: 4,
              decoration: BoxDecoration(
                color: Colors.grey[400],
                borderRadius: BorderRadius.circular(2),
              ),
            ),
          ),

          // Header + inline Reset
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 0, 8, 4),
            child: Row(
              children: [
                const Text('Filters', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
                const Spacer(),
                TextButton.icon(
                  icon: const Icon(Icons.clear_all, size: 18),
                  label: const Text('Reset'),
                  onPressed: _resetLocal,
                ),
              ],
            ),
          ),

          // Property
          ListTile(
            leading: const Icon(Icons.home_outlined),
            title: const Text('Property'),
            trailing: DropdownButton<int?>(
              isExpanded: false,
              value: _property,
              items: [
                const DropdownMenuItem(value: null, child: Text('All')),
                ...widget.properties.map(
                  (p) => DropdownMenuItem(value: p.id, child: Text(p.name)),
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
              isExpanded: false,
              value: _assignee,
              items: [
                const DropdownMenuItem(value: null, child: Text('All')),
                ...widget.assignees.map(
                  (u) => DropdownMenuItem(value: u.id, child: Text(u.username)),
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
                _from == null ? 'Any' : "${_from!.year}/${_from!.month}/${_from!.day}",
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
                _to == null ? 'Any' : "${_to!.year}/${_to!.month}/${_to!.day}",
              ),
            ),
          ),

          // Overdue checkbox
          CheckboxListTile(
            title: const Text('Only show overdue'),
            value: _overdue,
            onChanged: (v) => setState(() => _overdue = v ?? false),
            controlAffinity: ListTileControlAffinity.leading,
          ),

          const SizedBox(height: 8),

          // Footer buttons: Reset (apply & close) + Apply
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
            child: Row(
              children: [
                OutlinedButton.icon(
                  icon: const Icon(Icons.clear_all),
                  label: const Text('Reset'),
                  onPressed: () {
                    _resetLocal();
                    Navigator.pop(context);
                    widget.onApply(
                      property: null,
                      assignedTo: null,
                      dateFrom: null,
                      dateTo: null,
                      overdue: false,
                    );
                  },
                ),
                const Spacer(),
                ElevatedButton(
                  onPressed: () {
                    Navigator.pop(context);
                    widget.onApply(
                      property: _property,
                      assignedTo: _assignee,
                      dateFrom: _from,
                      dateTo: _to,
                      overdue: _overdue,
                    );
                  },
                  child: const Text('Apply Filters'),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}