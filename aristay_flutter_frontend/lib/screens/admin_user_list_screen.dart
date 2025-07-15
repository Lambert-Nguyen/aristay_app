import 'package:flutter/material.dart';
import '../models/user.dart';
import '../services/api_service.dart';

class AdminUserListScreen extends StatefulWidget {
  const AdminUserListScreen({Key? key}) : super(key: key);

  @override
  State<AdminUserListScreen> createState() => _AdminUserListScreenState();
}

class _AdminUserListScreenState extends State<AdminUserListScreen> {
  List<User> _users = [];
  bool _loading = true;
  String? _error;
  String?  _nextPageUrl;
  String   _searchQuery = '';

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load({ String? url, bool append = false }) async {
    try {
      setState(() => _loading = true);
      final resp = await ApiService().fetchUsers(url: url);
      setState(() {
        if (append) {
          _users.addAll(resp['results'] as List<User>);
        } else {
          _users = resp['results'] as List<User>;
        }
        _nextPageUrl = resp['next'] as String?;
      });
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      setState(() => _loading = false);
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
                Padding(
                  padding: const EdgeInsets.all(8),
                  child: TextField(
                    decoration: const InputDecoration(
                      labelText: 'Search by username or email',
                      prefixIcon: Icon(Icons.search),
                    ),
                    onSubmitted: (q) {
                      _searchQuery = q;
                      // build an absolute URL against your ApiService.baseUrl
                      final url = '${ApiService.baseUrl}/users/?search=${Uri.encodeQueryComponent(q)}';
                      // reset any old pagination
                      setState(() => _nextPageUrl = null);
                      _load(url: url, append: false);
                    },
                  ),
                ),
                Expanded(
                  child: ListView.builder(
                    itemCount: _users.length,
                    itemBuilder: (_, i) {
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
                if (_nextPageUrl != null)
                  TextButton(
                    onPressed: () => _load(url: _nextPageUrl, append: true),
                    child: const Text('Load more'),
                  ),
              ],
            ),
      floatingActionButton: FloatingActionButton(
        child: const Icon(Icons.person_add),
        onPressed: () async {
          final created =
            await Navigator.pushNamed(context, '/admin/create-user');
          if (created == true) _load();  // refresh list
        },
      ),
    );
  }
}