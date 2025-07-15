import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../models/user.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({Key? key}) : super(key: key);
  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  bool _loading = true;
  bool _isAdmin = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadCurrentUser();
  }

  Future<void> _loadCurrentUser() async {
    try {
      final user = await ApiService().fetchCurrentUser();
      setState(() {
        _isAdmin = user.isStaff == true;
      });
    } catch (e) {
      _error = e.toString();
    } finally {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return const Scaffold(
        body: Center(child: CircularProgressIndicator()),
      );
    }
    if (_error != null) {
      return Scaffold(
        body: Center(child: Text('Error: $_error')),
      );
    }

    return Scaffold(
      appBar: AppBar(title: const Text('Task Management')),
      body: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text('Welcome!'),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: () => Navigator.pushNamed(context, '/tasks'),
              child: const Text('View Tasks'),
            ),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: () async {
                final created =
                    await Navigator.pushNamed(context, '/create-task');
                if (created == true) {
                  Navigator.pushReplacementNamed(context, '/tasks');
                }
              },
              child: const Text('Create New Task'),
            ),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: () => Navigator.pushNamed(context, '/properties'),
              child: const Text('Manage Properties'),
            ),

            // ← only show to admins
            if (_isAdmin) ...[
              const SizedBox(height: 16),
              ElevatedButton.icon(
                icon: const Icon(Icons.admin_panel_settings),
                label: const Text('Admin Dashboard'),
                onPressed: () => Navigator.pushNamed(context, '/admin/users'),
              ),
            ],
          ],
        ),
      ),
    );
  }
}