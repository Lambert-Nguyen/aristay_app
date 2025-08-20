// lib/screens/admin_user_list_screen.dart
import 'dart:async';
import 'dart:math';

import 'package:flutter/material.dart';
import '../models/user.dart';
import '../services/api_service.dart';

class AdminUserListScreen extends StatefulWidget {
  const AdminUserListScreen({Key? key}) : super(key: key);

  @override
  State<AdminUserListScreen> createState() => _AdminUserListScreenState();
}

class _AdminUserListScreenState extends State<AdminUserListScreen> {
  // ───────── scrolling & data ─────────
  final ScrollController _scrollCtrl = ScrollController();
  List<User> _users = [];
  bool   _loading      = true;
  bool   _loadingMore  = false;
  String? _error;
  String? _nextPageUrl;
  String  _searchQuery = '';

  // ───────── highlight bookkeeping ─────────
  int? _highlightId;
  int? _highlightIndex;
  static const _rowHeight = 72.0;

  // ←─── NEW: flag so we only read args once
  bool _didReadArgs = false;

  @override
  void initState() {
    super.initState();
    _load();
    _scrollCtrl.addListener(_onScroll);
  }

  // ─────────────────────────────────────────────────────────
  //  SAFELY read ModalRoute args here
  // ─────────────────────────────────────────────────────────
  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (!_didReadArgs) {
      final args = ModalRoute.of(context)?.settings.arguments;
      if (args is Map && args['highlightUserId'] is int) {
        _highlightId = args['highlightUserId'] as int;
      }
      _didReadArgs = true;
    }
  }

  @override
  void dispose() {
    _scrollCtrl.removeListener(_onScroll);
    _scrollCtrl.dispose();
    super.dispose();
  }

  // ────────────────── infinite scroll helper ──────────────────
  void _onScroll() {
    if (_nextPageUrl != null &&
        !_loadingMore &&
        _scrollCtrl.position.pixels >
            0.9 * _scrollCtrl.position.maxScrollExtent) {
      // we're past 90% of the scroll
      _load(url: _nextPageUrl, append: true);
    }
  }

  // ────────────────── load / paginate ──────────────────
  Future<void> _load({String? url, bool append = false}) async {
    setState(() {
      append ? _loadingMore = true : _loading = true;
      if (!append) _error = null;
    });

    try {
      final resp    = await ApiService().fetchUsers(url: url);
      final results = resp['results'] as List<User>;
      setState(() {
        append ? _users.addAll(results) : _users = results;
        _nextPageUrl = resp['next'] as String?;
      });

      // scroll-to & tint once we know where the row is
      if (_highlightId != null && _highlightIndex == null) {
        final idx = _users.indexWhere((u) => u.id == _highlightId);
        if (idx != -1) {
          _highlightIndex = idx;
          WidgetsBinding.instance.addPostFrameCallback((_) {
            _scrollCtrl.animateTo(
              idx * _rowHeight,
              duration: const Duration(milliseconds: 300),
              curve: Curves.easeInOut,
            );
            // Clear highlight after a short flash so the list returns to normal
            Future.delayed(const Duration(milliseconds: 600), () {
              if (mounted) setState(() => _highlightId = null);
            });
          });
        }
      }
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      setState(() {
        _loading      = false;
        _loadingMore  = false;
      });
    }
  }

  // ────────────────── admin actions ──────────────────
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

  // ────────────────── UI ──────────────────
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
                    // ─── search box ───
                    Padding(
                      padding: const EdgeInsets.all(8),
                      child: TextField(
                        decoration: const InputDecoration(
                          labelText: 'Search by username or email',
                          prefixIcon: Icon(Icons.search),
                        ),
                        onSubmitted: (q) {
                          _searchQuery = q;
                          final url =
                              '${ApiService.baseUrl}/users/?search=${Uri.encodeQueryComponent(q)}';
                          _nextPageUrl = null;
                          _load(url: url, append: false);
                        },
                      ),
                    ),
                    // ─── list ───
                    Expanded(
                      child: ListView.builder(
                        controller: _scrollCtrl,
                        itemCount: _users.length + (_loadingMore ? 1 : 0),
                        itemBuilder: (_, i) {
                          if (i >= _users.length) {
                            return const Padding(
                              padding: EdgeInsets.symmetric(vertical: 16),
                              child: Center(child: CircularProgressIndicator()),
                            );
                          }
                          final u = _users[i];
                          return ListTile(
                            tileColor: u.id == _highlightId
                                ? Colors.yellow.withOpacity(0.30)
                                : null,
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
          final created =
              await Navigator.pushNamed(context, '/admin/create-user');
          if (created == true) _load();
        },
      ),
    );
  }
}