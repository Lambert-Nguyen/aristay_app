import 'package:flutter/material.dart';

import '../services/api_service.dart';

class AdminResetPasswordScreen extends StatefulWidget {
  const AdminResetPasswordScreen({Key? key}) : super(key: key);
  @override State<AdminResetPasswordScreen> createState() => _AdminResetPasswordScreenState();
}

class _AdminResetPasswordScreenState extends State<AdminResetPasswordScreen> {
  final _formKey = GlobalKey<FormState>();
  final _emailCtrl = TextEditingController();
  String? _error;
  bool _saving = false;

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    try {
      setState(() { _saving = true; _error = null; });
      await ApiService().resetUserPassword(_emailCtrl.text.trim());
      ScaffoldMessenger.of(context)
        .showSnackBar(const SnackBar(content: Text('Reset email sent')));
      Navigator.pop(context, true);
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext ctx) {
    return Scaffold(
      appBar: AppBar(title: const Text('Reset Password')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Form(
          key: _formKey,
          child: Column(
            children: [
              if (_error != null)
                Text(_error!, style: const TextStyle(color: Colors.red)),
              TextFormField(
                controller: _emailCtrl,
                decoration: const InputDecoration(labelText: 'User Email'),
                validator: (v) => v!.contains('@') ? null : 'Invalid email',
              ),
              const SizedBox(height: 24),
              _saving
                ? const CircularProgressIndicator()
                : ElevatedButton(onPressed: _submit, child: const Text('Send Reset')),
            ],
          ),
        ),
      ),
    );
  }
}