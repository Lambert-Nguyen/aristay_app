import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

class ApiService {
  static const String baseUrl = 'http://192.168.1.41:8000/api';

  Future<List<dynamic>?> fetchCleaningTasks() async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('auth_token');
    if (token == null) {
      throw Exception('No auth token found');
    }

    final uri = Uri.parse('$baseUrl/cleaning-tasks/');
    final response = await http.get(
      uri,
      headers: {
        'Authorization': 'Token $token',
      },
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      // data could be a List (no pagination) or a Map (pagination)
      if (data is List) {
        return data; // direct list of tasks
      } else if (data is Map && data.containsKey('results')) {
        return data['results']; // DRF pagination: use the "results" array
      } else {
        // Unexpected structure; return an empty list
        return [];
      }
    } else {
      throw Exception('Failed to load tasks. Status code: ${response.statusCode}');
    }
  }
}