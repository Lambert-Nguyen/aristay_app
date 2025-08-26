import 'package:flutter/material.dart';
import '../models/property.dart';
import '../services/api_service.dart';

class PropertyListScreen extends StatefulWidget {
  const PropertyListScreen({Key? key}) : super(key: key);

  @override
  State<PropertyListScreen> createState() => _PropertyListScreenState();
}

class _PropertyListScreenState extends State<PropertyListScreen> {
  final _api = ApiService();

  List<Property> _all = [];
  List<Property> _visible = [];
  bool _loading = false;
  String? _error;

  final _searchCtrl = TextEditingController();

  @override
  void initState() {
    super.initState();
    _load();
    _searchCtrl.addListener(_applySearch);
  }

  @override
  void dispose() {
    _searchCtrl.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final list = await _api.fetchProperties();
      _all = list;
      _applySearch();
    } catch (e) {
      _error = 'Failed to load properties';
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  void _applySearch() {
    final q = _searchCtrl.text.trim().toLowerCase();
    if (q.isEmpty) {
      setState(() => _visible = List.of(_all));
      return;
    }
    setState(() {
      _visible = _all.where((p) => p.name.toLowerCase().contains(q)).toList();
    });
  }

  Future<void> _confirmDelete(Property p) async {
    final yes = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Delete property?'),
        content: Text('“${p.name}” will be permanently removed.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancel')),
          TextButton(onPressed: () => Navigator.pop(context, true),  child: const Text('Delete')),
        ],
      ),
    );
    if (yes != true) return;

    final ok = await _api.deleteProperty(p.id);
    if (ok) {
      await _load();
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Property deleted')),
      );
    } else {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Delete failed')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Properties'),
        actions: [
          IconButton(
            tooltip: 'Refresh',
            icon: const Icon(Icons.refresh),
            onPressed: _load,
          ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? _ErrorState(message: _error!, onRetry: _load)
              : RefreshIndicator.adaptive(
                  onRefresh: _load,
                  child: ListView(
                    padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
                    children: [
                      // Search
                      TextField(
                        controller: _searchCtrl,
                        textInputAction: TextInputAction.search,
                        decoration: InputDecoration(
                          hintText: 'Search properties',
                          prefixIcon: const Icon(Icons.search),
                          filled: true,
                          fillColor: scheme.surface,
                          border: const OutlineInputBorder(
                            borderRadius: BorderRadius.all(Radius.circular(12)),
                          ),
                        ),
                      ),
                      const SizedBox(height: 12),

                      if (_visible.isEmpty)
                        _EmptyState(
                          title: _searchCtrl.text.isEmpty
                              ? 'No properties yet'
                              : 'No matches',
                          message: _searchCtrl.text.isEmpty
                              ? 'Create your first property to get started.'
                              : 'Try a different search term.',
                          actionLabel: _searchCtrl.text.isEmpty ? 'Create a property' : null,
                          onAction: _searchCtrl.text.isEmpty
                              ? () => Navigator.pushNamed(context, '/properties/new').then((_) => _load())
                              : null,
                        )
                      else
                        ..._visible.map((p) => _PropertyCard(
                              property: p,
                              onEdit: () {
                                Navigator.pushNamed(context, '/properties/edit', arguments: p)
                                    .then((_) => _load());
                              },
                              onDelete: () => _confirmDelete(p),
                            )),
                        SizedBox(height: MediaQuery.of(context).padding.bottom + 68),
                    ],
                  ),
                ),
      floatingActionButton: FloatingActionButton(
        tooltip: 'Add property',
        onPressed: () => Navigator.pushNamed(context, '/properties/new').then((_) => _load()),
        child: const Icon(Icons.add),
      ),
    );
  }
}

// ——— UI bits ————————————————————————————————————————————————

class _PropertyCard extends StatelessWidget {
  const _PropertyCard({
    required this.property,
    required this.onEdit,
    required this.onDelete,
  });

  final Property property;
  final VoidCallback onEdit;
  final VoidCallback onDelete;

  @override
  Widget build(BuildContext context) {
    final theme  = Theme.of(context);
    final scheme = theme.colorScheme;
    final onVar  = scheme.onSurface.withValues(alpha: .70);

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      elevation: 1,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: ListTile(
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
        leading: CircleAvatar(
          radius: 18,
          backgroundColor: scheme.surface,
          child: Text(
            (property.name.isNotEmpty ? property.name[0] : '?').toUpperCase(),
            style: const TextStyle(fontWeight: FontWeight.w700),
          ),
        ),
        title: Text(
          property.name,
          style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16.5),
        ),
        subtitle: Text('Property #${property.id}', style: TextStyle(color: onVar, fontSize: 13.5)),
        trailing: PopupMenuButton<String>(
          onSelected: (v) {
            if (v == 'edit') {
              onEdit();
            } else if (v == 'del') {
              onDelete();
            }
          },
          itemBuilder: (_) => const [
            PopupMenuItem(value: 'edit', child: ListTile(leading: Icon(Icons.edit), title: Text('Edit'))),
            PopupMenuItem(
              value: 'del',
              child: ListTile(
                leading: Icon(Icons.delete, color: Colors.redAccent),
                title: Text('Delete', style: TextStyle(color: Colors.redAccent)),
              ),
            ),
          ],
        ),
        onTap: onEdit,
      ),
    );
  }
}

class _EmptyState extends StatelessWidget {
  const _EmptyState({required this.title, required this.message, this.actionLabel, this.onAction});
  final String title;
  final String message;
  final String? actionLabel;
  final VoidCallback? onAction;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Card(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      elevation: 0,
      child: Padding(
        padding: const EdgeInsets.fromLTRB(16, 20, 16, 16),
        child: Column(
          children: [
            Icon(Icons.apartment_outlined, size: 56, color: scheme.primary),
            const SizedBox(height: 12),
            Text(title, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
            const SizedBox(height: 8),
            Text(message, textAlign: TextAlign.center),
            if (actionLabel != null) ...[
              const SizedBox(height: 12),
              FilledButton.icon(
                onPressed: onAction,
                icon: const Icon(Icons.add),
                label: Text(actionLabel!),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _ErrorState extends StatelessWidget {
  const _ErrorState({required this.message, required this.onRetry});
  final String message;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Card(
          color: scheme.errorContainer,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(mainAxisSize: MainAxisSize.min, children: [
              Icon(Icons.error_outline, color: scheme.onErrorContainer),
              const SizedBox(height: 8),
              Text(message, style: TextStyle(color: scheme.onErrorContainer)),
              const SizedBox(height: 12),
              FilledButton(
                onPressed: onRetry,
                child: const Text('Retry'),
              ),
            ]),
          ),
        ),
      ),
    );
  }
}