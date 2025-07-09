import 'package:flutter/material.dart';
import 'screens/login_screen.dart';
import 'screens/home_screen.dart';
import 'screens/task_list_screen.dart';
import 'screens/task_form_screen.dart';
import 'screens/edit_task_screen.dart';
import 'screens/task_detail_screen.dart';
import 'models/task.dart';

void main() => runApp(const MyApp());

class MyApp extends StatelessWidget {
  const MyApp({super.key});
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Aristay App',
      initialRoute: '/',
      routes: {
        '/': (c) => const LoginScreen(),
        '/home': (c) => const HomeScreen(),
        '/tasks': (c) => const TaskListScreen(),
        '/create-task': (c) => const TaskFormScreen(),
        '/edit-task': (c) {
          final task = ModalRoute.of(c)!.settings.arguments as Task;
          return EditTaskScreen(task: task);
        },
        '/task-detail': (c) {
          final task = ModalRoute.of(c)!.settings.arguments as Task;
          return TaskDetailScreen(task: task);
        },
      },
    );
  }
}