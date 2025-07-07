import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

class ApiService {
  // static const String baseUrl = 'http://192.168.1.41:8000/api';
  // static const String baseUrl = 'http://172.168.98.196:8000/api';
  static const String baseUrl = 'http://127.0.0.1:8000/api';

  // Returns a Map with "results" (List of tasks) and "next" (String?).
  Future<Map<String, dynamic>> fetchCleaningTasks({String? url}) async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('auth_token');
    if (token == null) {
      throw Exception('No auth token found');
    }

    final uri = url == null
        ? Uri.parse('$baseUrl/cleaning-tasks/') // First page
        : Uri.parse(url); // Next page

    final response = await http.get(
      uri,
      headers: {
        'Authorization': 'Token $token',
      },
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      // If pagination is enabled, data is a Map with "results".
      // If no pagination, data might be a List. We'll unify into a Map.
      if (data is List) {
        // No pagination
        return {
          'results': data,
          'next': null,
        };
      } else if (data is Map && data.containsKey('results')) {
        // Paginated response
        return {
          'results': data['results'],
          'next': data['next'],
        };
      } else {
        // Unexpected structure
        return {
          'results': <dynamic>[],
          'next': null,
        };
      }
    } else {
      throw Exception('Failed to load tasks. Status code: ${response.statusCode}');
    }
  }
  
  Future<bool> updateCleaningTask(int taskId, Map<String, dynamic> updatedData) async {
  final prefs = await SharedPreferences.getInstance();
  final token = prefs.getString('auth_token');
  if (token == null) {
    throw Exception('No auth token found');
  }

  final url = Uri.parse('$baseUrl/cleaning-tasks/$taskId/');
  final response = await http.patch(
    url,
    headers: {
      'Authorization': 'Token $token',
      'Content-Type': 'application/json',
    },
    body: jsonEncode(updatedData),
  );

  if (response.statusCode == 200) {
    return true;
  } else {
    print('Update failed. Status code: ${response.statusCode}');
    return false;
  }
}
}