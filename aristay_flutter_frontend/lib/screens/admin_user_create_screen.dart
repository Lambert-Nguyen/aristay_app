import 'package:flutter/material.dart';
import '../services/api_service.dart';

class AdminUserCreateScreen extends StatefulWidget {
  const AdminUserCreateScreen({Key? key}) : super(key: key);

  @override
  State<AdminUserCreateScreen> createState() => _AdminUserCreateScreenState();
}

class _AdminUserCreateScreenState extends State<AdminUserCreateScreen> {
  final _formKey = GlobalKey<FormState>();
  final _userCtrl = TextEditingController();
  final _emailCtrl = TextEditingController();
  final _passCtrl = TextEditingController();
  bool _isStaff = false;
  bool _loading = false;
  String? _error;
  Map<String,String>? _fieldErrors;

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() {
      _loading = true;
      _error = null;
      _fieldErrors = null;
    });
    try {
      await ApiService().createUser(
        username: _userCtrl.text.trim(),
        email: _emailCtrl.text.trim(),
        password: _passCtrl.text,
        isStaff: _isStaff,
      );
      Navigator.pop(context, true);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('User created'))
      );
    } on ValidationException catch (ve) {
      setState(() => _fieldErrors = ve.errors);
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      setState(() => _loading = false);
    }
  }

  @override
  void dispose() {
    _userCtrl.dispose();
    _emailCtrl.dispose();
    _passCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext ctx) {
    return Scaffold(
      appBar: AppBar(title: const Text('Admin: Create User')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Form(
          key: _formKey,
          child: ListView(children: [
            if (_error != null)
              Text(_error!, style: const TextStyle(color: Colors.red)),
            TextFormField(
              controller: _userCtrl,
              decoration: InputDecoration(
                labelText: 'Username',
                errorText: _fieldErrors?['username'],
              ),
              validator: (v) => v!.isEmpty ? 'Required' : null,
            ),
            const SizedBox(height: 16),
            TextFormField(
              controller: _emailCtrl,
              decoration: InputDecoration(
                labelText: 'Email',
                errorText: _fieldErrors?['email'],
              ),
              validator: (v) => v!.contains('@') ? null : 'Invalid email',
            ),
            const SizedBox(height: 16),
            TextFormField(
              controller: _passCtrl,
              decoration: InputDecoration(
                labelText: 'Password',
                errorText: _fieldErrors?['password'],
              ),
              obscureText: true,
              validator: (v) => v!.length < 8 ? 'Minimum 8 characters' : null,
            ),
            const SizedBox(height: 16),
            SwitchListTile(
              title: const Text('Staff / Admin privileges'),
              value: _isStaff,
              onChanged: (v) => setState(() => _isStaff = v),
            ),
            const SizedBox(height: 24),
            _loading
              ? const Center(child: CircularProgressIndicator())
              : ElevatedButton(
                  onPressed: _submit,
                  child: const Text('Create User'),
                ),
          ]),
        ),
      ),
    );
  }
}