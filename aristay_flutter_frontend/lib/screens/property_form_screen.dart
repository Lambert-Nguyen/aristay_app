import 'package:flutter/material.dart';
import '../models/property.dart';
import '../services/api_service.dart';

class PropertyFormScreen extends StatefulWidget {
  final Property? property;
  const PropertyFormScreen({Key? key, this.property}) : super(key: key);

  @override
  State<PropertyFormScreen> createState() => _PropertyFormScreenState();
}

class _PropertyFormScreenState extends State<PropertyFormScreen> {
  final _formKey = GlobalKey<FormState>();
  final _nameCtrl = TextEditingController();
  bool _loading = false, _error = false;

  @override
  void initState() {
    super.initState();
    if (widget.property != null) {
      _nameCtrl.text = widget.property!.name;
    }
  }

  Future<void> _save() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() {
      _loading = true;
      _error = false;
    });

    final payload = {'name': _nameCtrl.text.trim()};
    final api = ApiService();
    final ok = widget.property == null
        ? await api.createProperty(payload)
        : await api.updateProperty(widget.property!.id, payload);

    if (ok) {
      Navigator.pop(context, true);
    } else {
      setState(() => _error = true);
    }

    setState(() => _loading = false);
  }

  @override
  void dispose() {
    _nameCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final isEdit = widget.property != null;
    return Scaffold(
      appBar: AppBar(title: Text(isEdit ? 'Edit Property' : 'New Property')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Form(
          key: _formKey,
          child: Column(
            children: [
              TextFormField(
                controller: _nameCtrl,
                decoration: const InputDecoration(labelText: 'Name'),
                validator: (v) =>
                    (v ?? '').trim().isEmpty ? 'Required' : null,
              ),
              const SizedBox(height: 24),
              if (_error)
                const Text('Save failed',
                    style: TextStyle(color: Colors.red)),
              _loading
                  ? const CircularProgressIndicator()
                  : ElevatedButton(
                      onPressed: _save,
                      child: Text(isEdit ? 'Update' : 'Create'),
                    ),
            ],
          ),
        ),
      ),
    );
  }
}