import 'package:flutter/material.dart';
import '../models/property.dart';
import '../services/api_service.dart';

class PropertyListScreen extends StatefulWidget {
  const PropertyListScreen({Key? key}) : super(key: key);

  @override
  State<PropertyListScreen> createState() => _PropertyListScreenState();
}

class _PropertyListScreenState extends State<PropertyListScreen> {
  final ApiService _api = ApiService();
  List<Property> _items = [];
  bool _loading = false, _error = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    try {
      _items = await _api.fetchProperties();
      _error = false;
    } catch (_) {
      _error = true;
    } finally {
      setState(() => _loading = false);
    }
  }

  Future<void> _delete(Property p) async {
    final ok = await _api.deleteProperty(p.id);
    if (ok) {
      await _load();
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Delete failed')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Properties')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error
              ? const Center(child: Text('Failed to load properties'))
              : ListView.builder(
                  itemCount: _items.length,
                  itemBuilder: (ctx, i) {
                    final p = _items[i];
                    return ListTile(
                      title: Text(p.name),
                      trailing: PopupMenuButton<String>(
                        onSelected: (v) {
                          if (v == 'edit') {
                            Navigator.pushNamed(
                              context,
                              '/properties/edit',
                              arguments: p,
                            ).then((_) => _load());
                          } else if (v == 'del') {
                            _delete(p);
                          }
                        },
                        itemBuilder: (_) => const [
                          PopupMenuItem(value: 'edit', child: Text('Edit')),
                          PopupMenuItem(value: 'del', child: Text('Delete')),
                        ],
                      ),
                    );
                  },
                ),
      floatingActionButton: FloatingActionButton(
        onPressed: () {
          Navigator.pushNamed(context, '/properties/new')
              .then((_) => _load());
        },
        child: const Icon(Icons.add),
      ),
    );
  }
}