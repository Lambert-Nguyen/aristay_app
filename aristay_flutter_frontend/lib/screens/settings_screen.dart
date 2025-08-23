// lib/screens/settings_screen.dart
import 'package:flutter/material.dart';
import 'package:timezone/data/latest.dart' as tzdata;
import 'package:timezone/standalone.dart' as tz;
import '../services/api_service.dart';
import '../models/user.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({Key? key}) : super(key: key);

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  final _api = ApiService();
  final _formKey = GlobalKey<FormState>();

  User? _me;
  String? _selectedTz;
  late final TextEditingController _emailCtrl;
  late final TextEditingController _firstCtrl;  // ← add
  late final TextEditingController _lastCtrl;   // ← add

  bool _loading = true;
  bool _saving  = false;
  String? _error;
  List<String> _timezones = [];

  @override
  void initState() {
    super.initState();
    _emailCtrl = TextEditingController();
    _firstCtrl = TextEditingController();   // ← add
    _lastCtrl  = TextEditingController();   // ← add
    _initTimezones().then((_) => _loadUser());
  }

  @override
  void dispose() {
    _emailCtrl.dispose();
    _firstCtrl.dispose();   // ← add
    _lastCtrl.dispose();    // ← add
    super.dispose();
  }

  Future<void> _initTimezones() async {
    tzdata.initializeTimeZones();
    _timezones = tz.timeZoneDatabase.locations.keys.toList()..sort();
  }

  Future<void> _loadUser() async {
    try {
      final me = await _api.fetchCurrentUser();
      setState(() {
        _me           = me;
        _selectedTz   = me.timezone;
        _emailCtrl.text = me.email ?? '';
        _firstCtrl.text = me.firstName;   // ← add
        _lastCtrl.text  = me.lastName;    // ← add
        _error        = null;
      });
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      setState(() => _loading = false);
    }
  }

  bool get _dirty {
    if (_me == null) return false;
    final emailChanged = (_emailCtrl.text.trim() != (_me!.email ?? ''));
    final tzChanged    = (_selectedTz != _me!.timezone);
    final firstChanged = (_firstCtrl.text.trim() != _me!.firstName); // ← add
    final lastChanged  = (_lastCtrl.text.trim()  != _me!.lastName);  // ← add
    return emailChanged || tzChanged || firstChanged || lastChanged;
  }

  Future<void> _save() async {
    if (!_formKey.currentState!.validate()) return;
    if (!_dirty) return;

    setState(() { _saving = true; _error = null; });
    try {
      final emailTrim = _emailCtrl.text.trim();
      final firstTrim = _firstCtrl.text.trim();
      final lastTrim  = _lastCtrl.text.trim();

      final payloadTz   = (_selectedTz != _me!.timezone) ? _selectedTz : null;
      final payloadEmail= (emailTrim != (_me!.email ?? '')) ? emailTrim : null;
      final payloadFirst= (firstTrim != _me!.firstName) ? firstTrim : null; // ← add
      final payloadLast = (lastTrim  != _me!.lastName)  ? lastTrim  : null; // ← add

      final updated = await _api.updateCurrentUser(
        timezone: payloadTz,
        email:    payloadEmail,
        firstName: payloadFirst,   // ← add
        lastName:  payloadLast,    // ← add
      );

      if (!mounted) return;
      setState(() {
        _me           = updated;
        _selectedTz   = updated.timezone;
        _emailCtrl.text = updated.email ?? '';
        _firstCtrl.text = updated.firstName;  // ← add
        _lastCtrl.text  = updated.lastName;   // ← add
      });
      ScaffoldMessenger.of(context)
          .showSnackBar(const SnackBar(content: Text('Profile updated')));
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext ctx) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Profile'),
        actions: [
          TextButton.icon(
            onPressed: _saving || !_dirty ? null : _save,
            icon: const Icon(Icons.save),
            label: const Text('Save'),
            style: TextButton.styleFrom(
              foregroundColor: Theme.of(context).colorScheme.onPrimary,
            ),
          ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _loadUser,
              child: SingleChildScrollView(
                physics: const AlwaysScrollableScrollPhysics(),
                padding: const EdgeInsets.all(16),
                child: Form(
                  key: _formKey,
                  child: Column(
                    children: [
                      if (_error != null)
                        Padding(
                          padding: const EdgeInsets.only(bottom: 8.0),
                          child: Text(_error!, style: const TextStyle(color: Colors.red)),
                        ),
                      // Username (read-only context)
                      if (_me != null)
                        ListTile(
                          contentPadding: EdgeInsets.zero,
                          leading: const Icon(Icons.person_outline),
                          title: const Text('Username'),
                          subtitle: Text(_me!.username),
                        ),
                      const SizedBox(height: 8),
                      // First name
                      TextFormField(
                        controller: _firstCtrl,
                        decoration: const InputDecoration(
                          labelText: 'First name',
                          prefixIcon: Icon(Icons.badge_outlined),
                        ),
                        textCapitalization: TextCapitalization.words,
                        onChanged: (_) => setState(() {}),
                      ),

                      const SizedBox(height: 12),

                      // Last name
                      TextFormField(
                        controller: _lastCtrl,
                        decoration: const InputDecoration(
                          labelText: 'Last name',
                          prefixIcon: Icon(Icons.badge),
                        ),
                        textCapitalization: TextCapitalization.words,
                        onChanged: (_) => setState(() {}),
                      ),

                      const SizedBox(height: 16),

                      // Email (editable)
                      TextFormField(
                        controller: _emailCtrl,
                        decoration: const InputDecoration(
                          labelText: 'Email',
                          prefixIcon: Icon(Icons.alternate_email),
                        ),
                        keyboardType: TextInputType.emailAddress,
                        validator: (v) {
                          final s = (v ?? '').trim();
                          if (s.isEmpty) return 'Email is required';
                          final ok = RegExp(r'^[^@\s]+@[^@\s]+\.[^@\s]+$').hasMatch(s);
                          return ok ? null : 'Enter a valid email';
                        },
                        onChanged: (_) => setState(() {}),
                      ),
                      const SizedBox(height: 16),

                      // Timezone
                      DropdownButtonFormField<String>(
                        decoration: const InputDecoration(
                          labelText: 'Timezone',
                          prefixIcon: Icon(Icons.public),
                        ),
                        value: _selectedTz,
                        items: _timezones
                            .map((tz) => DropdownMenuItem(value: tz, child: Text(tz)))
                            .toList(),
                        onChanged: (v) => setState(() => _selectedTz = v),
                      ),
                      const SizedBox(height: 24),

                      // Big save button (for accessibility) — action button still in AppBar
                      SizedBox(
                        width: double.infinity,
                        child: ElevatedButton.icon(
                          icon: const Icon(Icons.save),
                          label: Text(_saving ? 'Saving…' : 'Save Changes'),
                          onPressed: _saving || !_dirty ? null : _save,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
    );
  }
}