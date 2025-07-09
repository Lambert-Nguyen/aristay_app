import 'package:flutter/material.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({Key? key}) : super(key: key);
  @override
  Widget build(BuildContext context) {
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
                final created = await Navigator.pushNamed(context, '/create-task');
                if (created == true) {
                  Navigator.pushReplacementNamed(context, '/tasks');
                }
              },
              child: const Text('Create New Task'),
            ),
          ],
        ),
      ),
    );
  }
}