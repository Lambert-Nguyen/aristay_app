import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';


class LoginScreen extends StatefulWidget {
  const LoginScreen({Key? key}) : super(key: key);
  @override
  _LoginScreenState createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final TextEditingController _usernameController = TextEditingController();
  final TextEditingController _passwordController = TextEditingController();
  bool _isLoading = false;
  String? _errorMessage;

  Future<void> _login() async {
    // Validate the form
    if (_formKey.currentState!.validate()) {
      setState(() {
        _isLoading = true;
        _errorMessage = null;
      });
      // Replace with your actual endpoint and IP address
      final url = Uri.parse('http://192.168.1.41:8000/api-token-auth/');
      try {
        final response = await http.post(
          url,
          body: {
            'username': _usernameController.text,
            'password': _passwordController.text,
          },
        );
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final token = data['token'];
        // Save the token using shared_preferences
        final prefs = await SharedPreferences.getInstance();
        await prefs.setString('auth_token', token);
        print('Logged in successfully, token: $token');
        // Navigate to the home screen
        Navigator.pushReplacementNamed(context, '/home');
      } else {
        setState(() {
          _errorMessage = 'Login failed. Please check your credentials.';
        });
      }
      } catch (error) {
        setState(() {
          _errorMessage = 'An error occurred. Please try again.';
        });
      } finally {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  @override
  void dispose() {
    _usernameController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Aristay Employee App Login')),
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16.0),
          child: Form(
            key: _formKey,
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                // 1. Add your logo image here
                Image.asset(
                  'assets/aristay_logo.jpg',  // Update path/filename as needed
                  width: 150,                // Adjust sizing to your preference
                  height: 150,
                ),
                const SizedBox(height: 24),

                // 2. Existing username field
                TextFormField(
                  controller: _usernameController,
                  decoration: const InputDecoration(labelText: 'Username'),
                  validator: (value) =>
                      value == null || value.isEmpty ? 'Please enter your username' : null,
                ),
                const SizedBox(height: 16),

                // 3. Existing password field
                TextFormField(
                  controller: _passwordController,
                  decoration: const InputDecoration(labelText: 'Password'),
                  obscureText: true,
                  validator: (value) =>
                      value == null || value.isEmpty ? 'Please enter your password' : null,
                ),
                const SizedBox(height: 24),

                if (_errorMessage != null)
                  Text(_errorMessage!, style: const TextStyle(color: Colors.red)),

                if (_isLoading)
                  const CircularProgressIndicator()
                else
                  ElevatedButton(
                    onPressed: _login,
                    child: const Text('Login'),
                  ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}