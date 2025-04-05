import 'package:flutter/material.dart';
import 'screens/login_screen.dart';
import 'screens/home_screen.dart';
import 'screens/task_list_screen.dart';
import 'screens/task_form_screen.dart';  // Import your task form screen

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({Key? key}) : super(key: key);
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Aristay App',
      initialRoute: '/',
      routes: {
        '/': (context) => const LoginScreen(),
        '/home': (context) => const HomeScreen(),
        '/tasks': (context) => const TaskListScreen(),
        '/create-task': (context) => const TaskFormScreen(), // New route for creating a task
      },
    );
  }
}