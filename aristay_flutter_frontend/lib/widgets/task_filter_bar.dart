import 'package:flutter/material.dart';
import '../models/property.dart';
import '../models/user.dart';

class TaskFilterBar extends StatefulWidget {
  final List<Property> properties;
  final List<User> assignees;
  final String selectedSearch;
  final String selectedStatus;
  final int? selectedProperty;
  final int? selectedAssignee;
  final DateTime? dateFrom;
  final DateTime? dateTo;
  final void Function({
    String? search,
    String? status,
    int? property,
    int? assignedTo,
    DateTime? dateFrom,
    DateTime? dateTo,
  }) onFilter;

  const TaskFilterBar({
    Key? key,
    required this.properties,
    required this.assignees,
    this.selectedSearch = '',
    this.selectedStatus = 'all',
    this.selectedProperty,
    this.selectedAssignee,
    this.dateFrom,
    this.dateTo,
    required this.onFilter,
  }) : super(key: key);

  @override
  State<TaskFilterBar> createState() => _TaskFilterBarState();
}

class _TaskFilterBarState extends State<TaskFilterBar> {
  late final TextEditingController _searchCtrl;
  late String _status;
  int? _propertyFilter;
  int? _assigneeFilter;
  DateTime? _dateFrom;
  DateTime? _dateTo;

  @override
  void initState() {
    super.initState();
    _searchCtrl = TextEditingController(text: widget.selectedSearch);
    _status = widget.selectedStatus;
    _propertyFilter = widget.selectedProperty;
    _assigneeFilter = widget.selectedAssignee;
    _dateFrom = widget.dateFrom;
    _dateTo = widget.dateTo;
  }

  @override
  void dispose() {
    _searchCtrl.dispose();
    super.dispose();
  }

  void _apply() {
    widget.onFilter(
      search: _searchCtrl.text.trim().isEmpty ? null : _searchCtrl.text.trim(),
      status: _status == 'all' ? null : _status,
      property: _propertyFilter,
      assignedTo: _assigneeFilter,
      dateFrom: _dateFrom,
      dateTo: _dateTo,
    );
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(8),
      child: Wrap(
        spacing: 8,
        runSpacing: 8,
        children: [
          // Search field
          SizedBox(
            width: 200,
            child: TextField(
              controller: _searchCtrl,
              decoration: const InputDecoration(
                labelText: 'Search…',
                prefixIcon: Icon(Icons.search),
              ),
              onSubmitted: (_) => _apply(),
            ),
          ),

          // Status dropdown
          DropdownButton<String>(
            value: _status,
            items: ['all', 'pending', 'in-progress', 'completed', 'canceled']
                .map((s) => DropdownMenuItem(
                      value: s,
                      child: Text(s == 'all' ? 'All' : s.replaceAll('-', ' ')),
                    ))
                .toList(),
            onChanged: (v) {
              if (v == null) return;
              setState(() => _status = v);
            },
          ),

          // Property dropdown
          DropdownButton<int?>(
            value: _propertyFilter,
            hint: const Text('Property'),
            items: [
              const DropdownMenuItem(value: null, child: Text('All')),
              ...widget.properties.map((p) => DropdownMenuItem(
                    value: p.id,
                    child: Text(p.name),
                  )),
            ],
            onChanged: (v) => setState(() => _propertyFilter = v),
          ),

          // Assignee dropdown
          DropdownButton<int?>(
            value: _assigneeFilter,
            hint: const Text('Assigned To'),
            items: [
              const DropdownMenuItem(value: null, child: Text('All')),
              ...widget.assignees.map((u) => DropdownMenuItem(
                    value: u.id,
                    child: Text(u.username),
                  )),
            ],
            onChanged: (v) => setState(() => _assigneeFilter = v),
          ),

          // Apply filter button
          IconButton(
            icon: const Icon(Icons.filter_alt),
            onPressed: _apply,
          ),
        ],
      ),
    );
  }
}