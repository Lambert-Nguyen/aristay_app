import 'package:flutter/material.dart';

import '../services/api_service.dart';

class AdminInviteScreen extends StatefulWidget {
  const AdminInviteScreen({Key? key}) : super(key: key);
  @override State<AdminInviteScreen> createState() => _AdminInviteScreenState();
}

class _AdminInviteScreenState extends State<AdminInviteScreen> {
  final _formKey = GlobalKey<FormState>();
  final _userCtrl = TextEditingController();
  final _emailCtrl = TextEditingController();
  Map<String,String> _errors = {};
  bool _saving = false;

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    try {
      setState(() { _saving = true; _errors = {}; });
      await ApiService()
        .inviteUser(_userCtrl.text.trim(), _emailCtrl.text.trim());
      ScaffoldMessenger.of(context)
        .showSnackBar(const SnackBar(content: Text('Invite sent!')));
      Navigator.pop(context, true);
    } on ValidationException catch (ve) {
      setState(() => _errors = ve.errors);
    } catch (e) {
      ScaffoldMessenger.of(context)
        .showSnackBar(SnackBar(content: Text(e.toString())));
    } finally {
      setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext ctx) {
    return Scaffold(
      appBar: AppBar(title: const Text('Invite User')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Form(
          key: _formKey,
          child: Column(
            children: [
              TextFormField(
                controller: _userCtrl,
                decoration: InputDecoration(
                  labelText: 'Username',
                  errorText: _errors['username'],
                ),
                validator: (v) => v!.isEmpty ? 'Required' : null,
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _emailCtrl,
                decoration: InputDecoration(
                  labelText: 'Email',
                  errorText: _errors['email'],
                ),
                validator: (v) => v!.contains('@') ? null : 'Invalid email',
              ),
              const SizedBox(height: 24),
              _saving
                ? const CircularProgressIndicator()
                : ElevatedButton(onPressed: _submit, child: const Text('Send')),
            ],
          ),
        ),
      ),
    );
  }
}