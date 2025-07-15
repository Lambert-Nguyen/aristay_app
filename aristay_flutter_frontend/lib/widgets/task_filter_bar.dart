import 'package:flutter/material.dart';

class TaskFilterBar extends StatefulWidget {
  final Function({
    String? search,
    int? property,
    String? status,
    int? assignedTo,
    DateTime? dateFrom,
    DateTime? dateTo,
  }) onFilter;

  const TaskFilterBar({required this.onFilter, Key? key}) : super(key: key);
  @override
  State<TaskFilterBar> createState() => _TaskFilterBarState();
}

class _TaskFilterBarState extends State<TaskFilterBar> {
  final _searchCtrl = TextEditingController();
  String _status = 'pending';
  // you can add property/assignee selectors here similarly

  void _apply() {
    widget.onFilter(
      search: _searchCtrl.text.trim().isEmpty ? null : _searchCtrl.text.trim(),
      status: _status,
      // property/assignedTo/date filters as you add them
    );
  }

  @override
  Widget build(BuildContext ctx) {
    return Padding(
      padding: const EdgeInsets.all(8),
      child: Row(children: [
        Expanded(
          child: TextField(
            controller: _searchCtrl,
            decoration: const InputDecoration(
              labelText: 'Search…',
              prefixIcon: Icon(Icons.search),
            ),
            onSubmitted: (_) => _apply(),
          ),
        ),
        const SizedBox(width: 8),
        DropdownButton<String>(
          value: _status,
          items: ['pending','in-progress','completed','canceled']
              .map((s) => DropdownMenuItem(value: s, child: Text(s)))
              .toList(),
          onChanged: (v) => setState(() => _status = v!),
        ),
        IconButton(icon: const Icon(Icons.filter_alt), onPressed: _apply),
      ]),
    );
  }
}