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
  final _formKey  = GlobalKey<FormState>();
  final _nameCtrl = TextEditingController();

  bool _saving = false;
  String? _pageError;

  bool get _isEdit => widget.property != null;

  @override
  void initState() {
    super.initState();
    if (_isEdit) _nameCtrl.text = widget.property!.name;
  }

  @override
  void dispose() {
    _nameCtrl.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() {
      _saving = true;
      _pageError = null;
    });

    final api = ApiService();
    final payload = {'name': _nameCtrl.text.trim()};

    bool ok = false;
    try {
      ok = _isEdit
          ? await api.updateProperty(widget.property!.id, payload)
          : await api.createProperty(payload);
    } catch (e) {
      _pageError = 'Save failed';
    }

    if (!mounted) return;

    setState(() => _saving = false);

    if (ok) {
      Navigator.pop(context, true);
    } else {
      setState(() => _pageError ??= 'Save failed');
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme  = Theme.of(context);
    final scheme = theme.colorScheme;

    return GestureDetector(
      onTap: () => FocusScope.of(context).unfocus(),
      child: Scaffold(
        appBar: AppBar(
          title: Text(_isEdit ? 'Edit Property' : 'New Property'),
        ),
        body: SafeArea(
          child: ListView(
            padding: const EdgeInsets.all(16),
            children: [
              if (_pageError != null)
                Card(
                  margin: const EdgeInsets.only(bottom: 12),
                  color: scheme.errorContainer,
                  child: Padding(
                    padding: const EdgeInsets.all(12),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Icon(Icons.error_outline, color: scheme.onErrorContainer),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(_pageError!, style: TextStyle(color: scheme.onErrorContainer)),
                        ),
                      ],
                    ),
                  ),
                ),

              _CardSection(
                icon: Icons.apartment_outlined,
                title: 'Details',
                child: Form(
                  key: _formKey,
                  child: TextFormField(
                    controller: _nameCtrl,
                    decoration: const InputDecoration(
                      labelText: 'Property name',
                      hintText: 'e.g., Maple Street Apartment 2B',
                    ),
                    textInputAction: TextInputAction.done,
                    validator: (v) => (v == null || v.trim().isEmpty) ? 'Required' : null,
                  ),
                ),
              ),

              if (_isEdit)
                Card(
                  margin: const EdgeInsets.only(top: 4),
                  elevation: 0,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  child: ListTile(
                    leading: const Icon(Icons.fingerprint),
                    title: Text('Property #${widget.property!.id}'),
                    subtitle: Text(
                      'Identifier',
                      style: TextStyle(color: scheme.onSurface.withValues(alpha: .70)),
                    ),
                  ),
                ),

              const SizedBox(height: 88),
            ],
          ),
        ),
        bottomNavigationBar: SafeArea(
          top: false,
          child: Padding(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 16),
            child: SizedBox(
              width: double.infinity,
              child: FilledButton.icon(
                onPressed: _saving ? null : _save,
                icon: _saving
                    ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))
                    : Icon(_isEdit ? Icons.save : Icons.add_task),
                label: Text(_isEdit ? 'Update Property' : 'Create Property'),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

// ——— Shared section card like in Task screens ————————————————

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
    final theme  = Theme.of(context);
    final scheme = theme.colorScheme;

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      elevation: 0,
      surfaceTintColor: scheme.surfaceTint,
      child: Padding(
        padding: const EdgeInsets.fromLTRB(16, 12, 16, 16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(children: [
              Icon(icon, size: 20, color: scheme.primary),
              const SizedBox(width: 8),
              Text(
                title,
                style: theme.textTheme.titleSmall?.copyWith(
                  color: scheme.onSurfaceVariant,
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