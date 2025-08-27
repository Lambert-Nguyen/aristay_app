import 'dart:math';
import 'package:flutter/material.dart';
import '../services/api_service.dart';

class AdminUserCreateScreen extends StatefulWidget {
  const AdminUserCreateScreen({Key? key}) : super(key: key);

  @override
  State<AdminUserCreateScreen> createState() => _AdminUserCreateScreenState();
}

class _AdminUserCreateScreenState extends State<AdminUserCreateScreen> {
  final _formKey  = GlobalKey<FormState>();
  final _userCtrl  = TextEditingController();
  final _emailCtrl = TextEditingController();
  final _passCtrl  = TextEditingController();

  bool _isStaff   = false;
  bool _saving    = false;
  String? _pageError;
  Map<String,String>? _fieldErrors;
  bool _showPw = false;

  @override
  void dispose() {
    _userCtrl.dispose();
    _emailCtrl.dispose();
    _passCtrl.dispose();
    super.dispose();
  }

  String _suggestPassword() {
    const letters = 'abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ';
    const digits  = '23456789';
    const symbols = '@#%+=!?';
    final rand = Random.secure();

    String pick(String s) => s[rand.nextInt(s.length)];
    String pickMany(String s, int n) =>
        List.generate(n, (_) => pick(s)).join();

    // 12–14 chars, at least one of each type
    final len = 12 + rand.nextInt(3);
    final pool = letters + digits + symbols;
    final core = List.generate(len - 3, (_) => pick(pool));
    final mix  = [
      pick(letters), pick(digits), pick(symbols), ...core,
    ]..shuffle(rand);
    return mix.join();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() {
      _saving = true;
      _pageError = null;
      _fieldErrors = null;
    });

    try {
      final newId = await ApiService().createUser(
        username: _userCtrl.text.trim(),
        email: _emailCtrl.text.trim(),
        password: _passCtrl.text,
        isStaff: _isStaff,
      );

      if (!mounted) return;
      // Return the new id so the list can auto-highlight and scroll.
      Navigator.pop(context, {'highlightUserId': newId});
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('User created')),
      );
    } on ValidationException catch (ve) {
      setState(() => _fieldErrors = ve.errors);
      // Keep form open; field errors render under inputs.
    } catch (e) {
      setState(() => _pageError = e.toString());
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  String? _validateEmail(String? v) {
    final s = (v ?? '').trim();
    if (s.isEmpty) return 'Required';
    final ok = RegExp(r'^[^@\s]+@[^@\s]+\.[^@\s]+$').hasMatch(s);
    return ok ? null : 'Invalid email';
  }

  @override
  Widget build(BuildContext context) {
    final theme  = Theme.of(context);
    final scheme = theme.colorScheme;

    return GestureDetector(
      onTap: () => FocusScope.of(context).unfocus(),
      child: Scaffold(
        appBar: AppBar(title: const Text('Admin: Create User')),
        body: SafeArea(
          child: ListView(
            padding: const EdgeInsets.all(16),
            children: [
              if (_pageError != null)
                Card(
                  margin: const EdgeInsets.only(bottom: 12),
                  color: scheme.errorContainer,
                  child: Padding(
                    padding: const EdgeInsets.all(12),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Icon(Icons.error_outline, color: scheme.onErrorContainer),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            _pageError!,
                            style: TextStyle(color: scheme.onErrorContainer),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),

              _CardSection(
                icon: Icons.person_outline,
                title: 'Account',
                child: Form(
                  key: _formKey,
                  autovalidateMode: AutovalidateMode.onUserInteraction,
                  child: Column(
                    children: [
                      TextFormField(
                        controller: _userCtrl,
                        decoration: InputDecoration(
                          labelText: 'Username',
                          errorText: _fieldErrors?['username'],
                        ),
                        textInputAction: TextInputAction.next,
                        validator: (v) => (v == null || v.trim().isEmpty) ? 'Required' : null,
                      ),
                      const SizedBox(height: 12),
                      TextFormField(
                        controller: _emailCtrl,
                        decoration: InputDecoration(
                          labelText: 'Email',
                          errorText: _fieldErrors?['email'],
                        ),
                        keyboardType: TextInputType.emailAddress,
                        textInputAction: TextInputAction.next,
                        validator: _validateEmail,
                      ),
                      const SizedBox(height: 12),
                      TextFormField(
                        controller: _passCtrl,
                        decoration: InputDecoration(
                          labelText: 'Password',
                          errorText: _fieldErrors?['password'],
                          suffixIcon: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              IconButton(
                                tooltip: _showPw ? 'Hide' : 'Show',
                                icon: Icon(_showPw ? Icons.visibility_off : Icons.visibility),
                                onPressed: () => setState(() => _showPw = !_showPw),
                              ),
                              IconButton(
                                tooltip: 'Suggest strong password',
                                icon: const Icon(Icons.auto_awesome),
                                onPressed: () {
                                  final pw = _suggestPassword();
                                  setState(() => _passCtrl.text = pw);
                                  ScaffoldMessenger.of(context).showSnackBar(
                                    const SnackBar(content: Text('Suggested a strong password')),
                                  );
                                },
                              ),
                            ],
                          ),
                        ),
                        obscureText: !_showPw,
                        validator: (v) =>
                            (v == null || v.length < 8) ? 'Minimum 8 characters' : null,
                      ),
                    ],
                  ),
                ),
              ),

              _CardSection(
                icon: Icons.admin_panel_settings_outlined,
                title: 'Permissions',
                child: SwitchListTile(
                  contentPadding: EdgeInsets.zero,
                  title: const Text('SuperStaff / Admin privileges'),
                  value: _isStaff,
                  onChanged: (v) => setState(() => _isStaff = v),
                ),
              ),

              const SizedBox(height: 88), // space for bottom bar
            ],
          ),
        ),
        bottomNavigationBar: SafeArea(
          top: false,
          child: Padding(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 16),
            child: SizedBox(
              width: double.infinity,
              child: FilledButton.icon(
                onPressed: _saving ? null : _submit,
                icon: _saving
                    ? const SizedBox(
                        width: 18, height: 18,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.person_add),
                label: const Text('Create User'),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

// Shared section card (matches Tasks/Properties look)
class _CardSection extends StatelessWidget {
  const _CardSection({required this.icon, required this.title, required this.child});
  final IconData icon;
  final String title;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    final theme  = Theme.of(context);
    final scheme = theme.colorScheme;
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      elevation: 0,
      surfaceTintColor: scheme.surfaceTint,
      child: Padding(
        padding: const EdgeInsets.fromLTRB(16, 12, 16, 16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(children: [
              Icon(icon, size: 20, color: scheme.primary),
              const SizedBox(width: 8),
              Text(
                title,
                style: theme.textTheme.titleSmall?.copyWith(
                  color: scheme.onSurfaceVariant,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ]),
            const SizedBox(height: 12),
            child,
          ],
        ),
      ),
    );
  }
}