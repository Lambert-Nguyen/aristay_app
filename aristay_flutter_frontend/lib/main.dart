import 'package:flutter/material.dart';
import 'models/task.dart';
import 'models/property.dart';

import 'screens/login_screen.dart';
import 'screens/home_screen.dart';
import 'screens/task_list_screen.dart';
import 'screens/task_form_screen.dart';
import 'screens/edit_task_screen.dart';
import 'screens/task_detail_screen.dart';
import 'screens/property_list_screen.dart';
import 'screens/property_form_screen.dart';
import 'screens/admin_invite_screen.dart';
import 'screens/admin_reset_password_screen.dart';
import 'screens/admin_user_list_screen.dart';
import 'screens/admin_user_create_screen.dart';


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
        '/properties': (c) => const PropertyListScreen(),
        '/properties/new': (c) => const PropertyFormScreen(),
        '/properties/edit': (c) {
          final prop = ModalRoute.of(c)!.settings.arguments as Property;
          return PropertyFormScreen(property: prop);
        },
        '/create-task': (c) => const TaskFormScreen(),
        '/edit-task': (c) {
          final task = ModalRoute.of(c)!.settings.arguments as Task;
          return EditTaskScreen(task: task);
        },
        '/task-detail': (c) {
          final task = ModalRoute.of(c)!.settings.arguments as Task;
          return TaskDetailScreen(initialTask: task);
        },
        // Admin user management
        '/admin/users': (c) => const AdminUserListScreen(),
        '/admin/invite': (c) => const AdminInviteScreen(),
        '/admin/reset-password': (c) => const AdminResetPasswordScreen(),
        '/admin/create-user': (c) => const AdminUserCreateScreen(),
      },
    );
  }
}