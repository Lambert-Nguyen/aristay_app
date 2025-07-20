// lib/screens/settings_screen.dart

import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:timezone/data/latest.dart' as tzdata;  // add timezone package to pubspec
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
  User?   _me;
  String? _selectedTz;
  bool    _loading = true;
  bool    _saving  = false;
  String? _error;

  List<String> _timezones = [];

  @override
  void initState() {
    super.initState();
    _initTimezones().then((_) => _loadUser());
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
        _error        = null;
      });
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      setState(() => _loading = false);
    }
  }

  Future<void> _save() async {
    if (_selectedTz == null) return;
    setState(() {
      _saving = true;
      _error  = null;
    });
    try {
      final updated = await _api.updateCurrentUser(timezone: _selectedTz!);
      // optionally persist in prefs or refresh global state
      ScaffoldMessenger.of(context)
          .showSnackBar(const SnackBar(content: Text('Timezone saved')));
      setState(() {
        _me         = updated;
        _selectedTz = updated.timezone;
      });
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext ctx) {
    return Scaffold(
      appBar: AppBar(title: const Text('Settings')),
      body: _loading
        ? const Center(child: CircularProgressIndicator())
        : Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              children: [
                if (_error != null)
                  Text(_error!, style: const TextStyle(color: Colors.red)),
                const SizedBox(height: 16),
                DropdownButtonFormField<String>(
                  decoration: const InputDecoration(labelText: 'Timezone'),
                  value: _selectedTz,
                  items: _timezones.map((tz) =>
                    DropdownMenuItem(value: tz, child: Text(tz))
                  ).toList(),
                  onChanged: (v) => setState(() => _selectedTz = v),
                ),
                const SizedBox(height: 24),
                _saving
                  ? const CircularProgressIndicator()
                  : ElevatedButton(
                      onPressed: _save,
                      child: const Text('Save'),
                    ),
              ],
            ),
          ),
    );
  }
}