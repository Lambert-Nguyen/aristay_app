// lib/screens/admin_user_list_screen.dart

import 'package:flutter/material.dart';
import '../models/user.dart';
import '../services/api_service.dart';

class AdminUserListScreen extends StatefulWidget {
  const AdminUserListScreen({Key? key}) : super(key: key);

  @override
  State<AdminUserListScreen> createState() => _AdminUserListScreenState();
}

class _AdminUserListScreenState extends State<AdminUserListScreen> {
  final ScrollController _scrollCtrl = ScrollController();

  List<User> _users = [];
  bool _loading = true;
  bool _loadingMore = false;
  String? _error;
  String? _nextPageUrl;
  String _searchQuery = '';

  @override
  void initState() {
    super.initState();
    _load();
    _scrollCtrl.addListener(_onScroll);
  }

  @override
  void dispose() {
    _scrollCtrl.removeListener(_onScroll);
    _scrollCtrl.dispose();
    super.dispose();
  }

  void _onScroll() {
    if (_nextPageUrl != null &&
        !_loadingMore &&
        _scrollCtrl.position.pixels >
            0.9 * _scrollCtrl.position.maxScrollExtent) {
      // we're past 90% of the scroll
      _load(url: _nextPageUrl, append: true);
    }
  }

  Future<void> _load({ String? url, bool append = false }) async {
    setState(() {
      if (append) {
        _loadingMore = true;
      } else {
        _loading = true;
        _error = null;
      }
    });

    try {
      final resp = await ApiService().fetchUsers(url: url);
      final results = resp['results'] as List<User>;
      setState(() {
        if (append) {
          _users.addAll(results);
        } else {
          _users = results;
        }
        _nextPageUrl = resp['next'] as String?;
      });
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      setState(() {
        _loading = false;
        _loadingMore = false;
      });
    }
  }

  Future<void> _reset(User u) async {
    try {
      await ApiService().resetUserPassword(u.email!);
      ScaffoldMessenger.of(context)
        .showSnackBar(const SnackBar(content: Text('Reset email sent')));
    } catch (e) {
      ScaffoldMessenger.of(context)
        .showSnackBar(SnackBar(content: Text(e.toString())));
    }
  }

  @override
  Widget build(BuildContext ctx) {
    return Scaffold(
      appBar: AppBar(title: const Text('Admin: Users')),
      body: _loading
        ? const Center(child: CircularProgressIndicator())
        : _error != null
          ? Center(child: Text(_error!))
          : Column(
              children: [
                // Search field
                Padding(
                  padding: const EdgeInsets.all(8),
                  child: TextField(
                    decoration: const InputDecoration(
                      labelText: 'Search by username or email',
                      prefixIcon: Icon(Icons.search),
                    ),
                    onSubmitted: (q) {
                      _searchQuery = q;
                      final url = '${ApiService.baseUrl}/users/?search=${Uri.encodeQueryComponent(q)}';
                      setState(() {
                        _nextPageUrl = null;
                      });
                      _load(url: url, append: false);
                    },
                  ),
                ),

                // Infinite‐scroll list
                Expanded(
                  child: ListView.builder(
                    controller: _scrollCtrl,
                    itemCount: _users.length + (_loadingMore ? 1 : 0),
                    itemBuilder: (_, i) {
                      if (i >= _users.length) {
                        // loading‐more indicator at bottom
                        return const Padding(
                          padding: EdgeInsets.symmetric(vertical: 16),
                          child: Center(child: CircularProgressIndicator()),
                        );
                      }
                      final u = _users[i];
                      return ListTile(
                        title: Text(u.username),
                        subtitle: Text(u.email ?? ''),
                        trailing: IconButton(
                          icon: const Icon(Icons.lock_reset),
                          onPressed: () => _reset(u),
                        ),
                      );
                    },
                  ),
                ),
              ],
            ),
      floatingActionButton: FloatingActionButton(
        child: const Icon(Icons.person_add),
        onPressed: () async {
          final created = await Navigator.pushNamed(context, '/admin/create-user');
          if (created == true) _load();
        },
      ),
    );
  }
}