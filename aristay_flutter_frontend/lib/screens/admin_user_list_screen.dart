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

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      setState(() => _loading = true);
      final users = await ApiService().fetchUsers();
      setState(() => _users = users);
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
          : ListView.builder(
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