import 'package:flutter/material.dart';
import 'services/api_service.dart';

void main() {
  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  final ApiService apiService = ApiService();

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Aristay Cleaning Tasks',
      home: Scaffold(
        appBar: AppBar(
          title: Text('Cleaning Tasks'),
        ),
        body: FutureBuilder<List<dynamic>?>(
          future: apiService.fetchCleaningTasks(),
          builder: (context, snapshot) {
            if (snapshot.connectionState == ConnectionState.waiting) {
              return Center(child: CircularProgressIndicator());
            } else if (snapshot.hasError) {
              return Center(child: Text('Error fetching tasks'));
            } else if (!snapshot.hasData || snapshot.data!.isEmpty) {
              return Center(child: Text('No tasks available'));
            } else {
              final tasks = snapshot.data!;
              return ListView.builder(
                itemCount: tasks.length,
                itemBuilder: (context, index) {
                  final task = tasks[index];
                  return ListTile(
                    title: Text(task['property_name'] ?? 'Unnamed'),
                    subtitle: Text('Status: ${task['status']}'),
                  );
                },
              );
            }
          },
        ),
      ),
    );
  }
}
