// lib/screens/admin_user_list_screen.dart
import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../models/user.dart';
import '../services/api_service.dart';
import '../utils/api_error.dart';

class AdminUserListScreen extends StatefulWidget {
  const AdminUserListScreen({Key? key}) : super(key: key);

  @override
  State<AdminUserListScreen> createState() => _AdminUserListScreenState();
}

class _AdminUserListScreenState extends State<AdminUserListScreen> {
  // data + paging
  final _scrollCtrl = ScrollController();
  final _searchCtrl = TextEditingController();
  Timer? _debounce;

  List<User> _users = [];
  String? _nextUrl;
  int _totalCount = 0;

  bool _loading = true;
  bool _loadingMore = false;
  String? _error;

  // filters
  bool _adminsOnly = false;

  // highlight newly created user (optional)
  int? _highlightId;
  int? _highlightIndex;
  static const _rowHeight = 86.0;

  bool _didReadArgs = false;

  @override
  void initState() {
    super.initState();
    _load();
    _scrollCtrl.addListener(_onScroll);
    _searchCtrl.addListener(_onSearchChanged);
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (_didReadArgs) return;
    final args = ModalRoute.of(context)?.settings.arguments;
    if (args is Map && args['highlightUserId'] is int) {
      _highlightId = args['highlightUserId'] as int;
    }
    _didReadArgs = true;
  }

  @override
  void dispose() {
    _scrollCtrl.removeListener(_onScroll);
    _scrollCtrl.dispose();
    _searchCtrl.removeListener(_onSearchChanged);
    _searchCtrl.dispose();
    _debounce?.cancel();
    super.dispose();
  }

  // ─────────────────────── data ───────────────────────

  Future<void> _load({String? url, bool append = false}) async {
    setState(() {
      if (append) {
        _loadingMore = true;
      } else {
        _loading = true;
        _error = null;
      }
    });

    try {
      final res = await ApiService().fetchUsers(url: url);
      final page = (res['results'] as List<User>);
      setState(() {
        if (append) {
          _users.addAll(page);
        } else {
          _users = page;
        }
        _nextUrl = res['next'] as String?;
        _totalCount = (res['count'] as int?) ?? _users.length;
      });

      // if we got a highlight target and haven't scrolled yet, do it once
      if (_highlightId != null && _highlightIndex == null) {
        final idx = _users.indexWhere((u) => u.id == _highlightId);
        if (idx != -1) {
          _highlightIndex = idx;
          WidgetsBinding.instance.addPostFrameCallback((_) {
            _scrollCtrl.animateTo(
              idx * _rowHeight,
              duration: const Duration(milliseconds: 350),
              curve: Curves.easeInOut,
            );
            Future.delayed(const Duration(milliseconds: 700), () {
              if (mounted) setState(() => _highlightId = null);
            });
          });
        }
      }
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      if (!mounted) return;
      setState(() {
        _loading = false;
        _loadingMore = false;
      });
      // auto top-up if first page doesn't fill the viewport
      WidgetsBinding.instance.addPostFrameCallback((_) => _maybeTopUp());
    }
  }

  void _maybeTopUp() {
    if (!_scrollCtrl.hasClients || _loadingMore || _nextUrl == null) return;
    final canScroll = _scrollCtrl.position.maxScrollExtent > 0;
    if (!canScroll) _load(url: _nextUrl, append: true);
  }

  void _onScroll() {
    if (_nextUrl != null &&
        !_loadingMore &&
        _scrollCtrl.position.pixels >
            _scrollCtrl.position.maxScrollExtent * 0.90) {
      _load(url: _nextUrl, append: true);
    }
  }

  void _onSearchChanged() {
    _debounce?.cancel();
    _debounce = Timer(const Duration(milliseconds: 300), () {
      final q = _searchCtrl.text.trim();
      final url = q.isEmpty
          ? '${ApiService.baseUrl}/users/'
          : '${ApiService.baseUrl}/users/?search=${Uri.encodeQueryComponent(q)}';
      _nextUrl = null;
      _load(url: url, append: false);
    });
  }

  Future<void> _refresh() async {
    final q = _searchCtrl.text.trim();
    final url = q.isEmpty
        ? '${ApiService.baseUrl}/users/'
        : '${ApiService.baseUrl}/users/?search=${Uri.encodeQueryComponent(q)}';
    await _load(url: url, append: false);
  }

  // ───────────────── admin actions ─────────────────

  Future<void> _resetPassword(User u) async {
    if ((u.email ?? '').isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('This user has no email to reset.')),
      );
      return;
    }
    try {
      await ApiService().resetUserPassword(u.email!);
      if (!mounted) return;
      ScaffoldMessenger.of(context)
          .showSnackBar(const SnackBar(content: Text('Reset email sent')));
    } on ValidationException catch (ve) {
      // server-side field errors
      final msg = ve.errors.values.join(' ');
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg)));
    } catch (e) {
      showFriendlyError(context, e, action: 'send a reset email');
    }
  }

  Future<void> _toggleActive(User u) async {
    final next = !u.isActive;
    final yes = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: Text(next ? 'Enable account?' : 'Disable account?'),
        content: Text(next
            ? 'User will be able to sign in again.'
            : 'User will be signed out and cannot sign in until re-enabled.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancel')),
          TextButton(onPressed: () => Navigator.pop(context, true),  child: Text(next ? 'Enable' : 'Disable')),
        ],
      ),
    );
    if (yes != true) return;

    try {
      await ApiService().setUserActive(u.id, next);
      final idx = _users.indexWhere((x) => x.id == u.id);
      if (idx != -1) setState(() => _users[idx] = _users[idx].copyWith(isActive: next));
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(next ? 'User enabled' : 'User disabled')),
      );
    } catch (e) {
      showFriendlyError(context, e, action: next ? 'enable this user' : 'disable this user');
    }
  }

  // ─────────────────────── UI ───────────────────────

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Admin: Users'),
        actions: [
          IconButton(
            tooltip: 'Refresh',
            icon: const Icon(Icons.refresh),
            onPressed: _refresh,
          ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? _ErrorState(message: _error!, onRetry: _refresh)
              : RefreshIndicator.adaptive(
                  onRefresh: _refresh,
                  child: ListView(
                    controller: _scrollCtrl,
                    padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
                    physics: const AlwaysScrollableScrollPhysics(),
                    children: [
                      // search
                      TextField(
                        controller: _searchCtrl,
                        textInputAction: TextInputAction.search,
                        decoration: InputDecoration(
                          hintText: 'Search by username or email',
                          prefixIcon: const Icon(Icons.search),
                          suffixIcon: _searchCtrl.text.isEmpty
                              ? null
                              : IconButton(
                                  tooltip: 'Clear',
                                  icon: const Icon(Icons.clear),
                                  onPressed: () {
                                    _searchCtrl.clear();
                                    _onSearchChanged();
                                  },
                                ),
                          filled: true,
                          fillColor: scheme.surface,
                          border: const OutlineInputBorder(
                            borderRadius: BorderRadius.all(Radius.circular(12)),
                          ),
                        ),
                      ),
                      const SizedBox(height: 8),

                      // filters row
                      Wrap(
                        spacing: 8,
                        runSpacing: 8,
                        children: [
                          FilterChip(
                            label: const Text('Admins only'),
                            selected: _adminsOnly,
                            onSelected: (v) => setState(() => _adminsOnly = v),
                          ),
                        ],
                      ),
                      const SizedBox(height: 6),

                      // counts
                      _CountHeader(
                        loaded: _users.length,
                        total: _totalCount,
                        showing: _visibleUsers.length,
                        filtered: _adminsOnly,
                      ),
                      const SizedBox(height: 8),

                      if (_visibleUsers.isEmpty)
                        _EmptyState(
                          title: 'No users',
                          message: _searchCtrl.text.isEmpty
                              ? 'Create a new account to get started.'
                              : 'Try a different search term.',
                        )
                      else
                        ..._visibleUsers.map((u) => _UserCard(
                              user: u,
                              highlight: u.id == _highlightId,
                              onReset: () => _resetPassword(u),
                              onToggleActive: () => _toggleActive(u),
                              onCopyUsername: () => _copy(u.username, 'Username copied'),
                              onCopyEmail: (u.email ?? '').isEmpty
                                  ? null
                                  : () => _copy(u.email!, 'Email copied'),
                            )),

                      // footer spinner if loading more
                      if (_loadingMore)
                        const Padding(
                          padding: EdgeInsets.symmetric(vertical: 16),
                          child: Center(child: CircularProgressIndicator()),
                        ),

                      // spacer so FAB never overlaps last row
                      SizedBox(height: MediaQuery.of(context).padding.bottom + 72),
                    ],
                  ),
                ),
      floatingActionButton: FloatingActionButton(
        tooltip: 'Create user',
        onPressed: () async {
          final res = await Navigator.pushNamed(context, '/admin/create-user');
          if (res is Map && res['highlightUserId'] is int) {
            // highlight + refresh
            setState(() => _highlightId = res['highlightUserId'] as int);
            await _refresh();
          } else if (res == true) {
            // backward-compat
            _refresh();
          }
        },
        child: const Icon(Icons.person_add),
      ),
    );
  }

  List<User> get _visibleUsers =>
      _adminsOnly ? _users.where((u) => u.isStaff).toList() : _users;

  void _copy(String text, String toast) {
    Clipboard.setData(ClipboardData(text: text));
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(toast)));
  }
}

// ─────────────────────── widgets ───────────────────────

class _UserCard extends StatelessWidget {
  const _UserCard({
    required this.user,
    required this.onReset,
    required this.onCopyUsername,
    this.onCopyEmail,
    required this.onToggleActive,
    this.highlight = false,
  });

  final User user;
  final VoidCallback onReset;
  final VoidCallback onCopyUsername;
  final VoidCallback? onCopyEmail;
  final VoidCallback onToggleActive;
  final bool highlight;

  @override
  Widget build(BuildContext context) {
    final theme  = Theme.of(context);
    final scheme = theme.colorScheme;
    final onVar  = scheme.onSurface.withValues(alpha: .70);

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      elevation: 1,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      color: !user.isActive
          ? theme.colorScheme.errorContainer.withValues(alpha:.18)
          : (highlight ? scheme.primary.withValues(alpha: .08) : null),
      child: ListTile(
        contentPadding: const EdgeInsets.fromLTRB(16, 12, 8, 12),
        leading: CircleAvatar(
          radius: 20,
          backgroundColor: scheme.surface,
          child: Text(
            _initials(user),
            style: const TextStyle(fontWeight: FontWeight.w800),
          ),
        ),
        title: Row(
          children: [
            Expanded(
              child: Text(
                user.username,
                style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16.5),
              ),
            ),
            if (!user.isActive)
              _Badge('Disabled', color: Colors.redAccent),
            if (user.isStaff)
              _Badge('Admin', color: scheme.primary),
          ],
        ),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if ((user.firstName?.isNotEmpty ?? false) ||
                (user.lastName?.isNotEmpty ?? false))
              Text(
                '${user.firstName ?? ''} ${user.lastName ?? ''}'.trim(),
                style: theme.textTheme.bodySmall,
              ),
            if ((user.email ?? '').isNotEmpty)
              Text(user.email!, style: theme.textTheme.bodySmall?.copyWith(color: onVar)),
          ],
        ),
        trailing: PopupMenuButton<String>(
          tooltip: 'Actions',
          onSelected: (v) {
            switch (v) {
              case 'reset': onReset(); break;
              case 'copy_u': onCopyUsername(); break;
              case 'copy_e': if (onCopyEmail != null) onCopyEmail!(); break;
              case 'toggle':  onToggleActive(); break;
            }
          },
          itemBuilder: (_) => [
            const PopupMenuItem(
              value: 'reset',
              child: ListTile(
                leading: Icon(Icons.key),
                title: Text('Send password reset'),
              ),
            ),
            const PopupMenuItem(
              value: 'copy_u',
              child: ListTile(
                leading: Icon(Icons.copy),
                title: Text('Copy username'),
              ),
            ),
            PopupMenuItem(
              enabled: onCopyEmail != null,
              value: 'copy_e',
              child: const ListTile(
                leading: Icon(Icons.email),
                title: Text('Copy email'),
              ),
            ),
            PopupMenuItem(
              value: 'toggle',
              child: ListTile(
                leading: Icon(user.isActive ? Icons.person_off : Icons.person),
                title: Text(user.isActive ? 'Disable account' : 'Enable account'),
              ),
            ),
          ],
        ),
      ),
    );
  }

  String _initials(User u) {
    final fn = (u.firstName ?? '').trim();
    final ln = (u.lastName ?? '').trim();
    if (fn.isNotEmpty || ln.isNotEmpty) {
      return '${fn.isNotEmpty ? fn[0] : ''}${ln.isNotEmpty ? ln[0] : ''}'.toUpperCase();
    }
    return u.username.isNotEmpty ? u.username[0].toUpperCase() : '?';
    }
}

class _Badge extends StatelessWidget {
  const _Badge(this.text, {this.color});
  final String text;
  final Color? color;

  @override
  Widget build(BuildContext context) {
    final c = color ?? Theme.of(context).colorScheme.primary;
    return Container(
      margin: const EdgeInsets.only(left: 8),
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: c.withOpacity(.12),
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: c),
      ),
      child: Text(text, style: TextStyle(color: c, fontWeight: FontWeight.w700, fontSize: 12)),
    );
  }
}

class _CountHeader extends StatelessWidget {
  const _CountHeader({
    required this.loaded,
    required this.total,
    required this.showing,
    required this.filtered,
  });
  final int loaded;
  final int total;
  final int showing;
  final bool filtered;

  @override
  Widget build(BuildContext context) {
    final grey = Theme.of(context).colorScheme.onSurface.withValues(alpha: .65);
    final text = filtered
        ? 'Loaded $loaded of $total • showing $showing'
        : 'Loaded $loaded of $total';
    return Padding(
      padding: const EdgeInsets.fromLTRB(4, 2, 4, 0),
      child: Text(text, style: TextStyle(fontSize: 13, color: grey)),
    );
  }
}

class _EmptyState extends StatelessWidget {
  const _EmptyState({required this.title, required this.message});
  final String title;
  final String message;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Card(
      margin: const EdgeInsets.only(top: 8),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      elevation: 0,
      child: Padding(
        padding: const EdgeInsets.fromLTRB(16, 20, 16, 16),
        child: Column(
          children: [
            Icon(Icons.people_outline, size: 56, color: scheme.primary),
            const SizedBox(height: 12),
            Text(title, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
            const SizedBox(height: 8),
            Text(message, textAlign: TextAlign.center),
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
              FilledButton(onPressed: onRetry, child: const Text('Retry')),
            ]),
          ),
        ),
      ),
    );
  }
}