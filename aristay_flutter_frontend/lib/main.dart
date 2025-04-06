import 'package:flutter/material.dart';
import 'screens/login_screen.dart';
import 'screens/home_screen.dart';
import 'screens/task_list_screen.dart';
import 'screens/task_form_screen.dart';
import 'screens/edit_task_screen.dart';
import 'screens/task_detail_screen.dart'; // Import the detail screen

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
        '/create-task': (context) => const TaskFormScreen(),
        '/edit-task': (context) {
          final task = ModalRoute.of(context)!.settings.arguments as Map<String, dynamic>;
          return EditTaskScreen(task: task);
        },
        '/task-detail': (context) {
          final task = ModalRoute.of(context)!.settings.arguments as Map<String, dynamic>;
          return TaskDetailScreen(task: task);
        },
      },
    );
  }
}