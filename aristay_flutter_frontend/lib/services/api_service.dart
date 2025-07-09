import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../models/property.dart';
import '../models/task.dart';

class ApiService {
  static const String baseUrl = 'http://127.0.0.1:8000/api';

  Future<List<Property>> fetchProperties() async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('auth_token');
    if (token == null) throw Exception('No auth token found');

    final res = await http.get(
      Uri.parse('$baseUrl/properties/'),
      headers: {'Authorization': 'Token $token'},
    );
    if (res.statusCode != 200) {
      throw Exception('Failed to load properties (${res.statusCode})');
    }
    final body = jsonDecode(res.body);
    final raw = body is List ? body : (body['results'] as List<dynamic>);
    return raw.map((e) => Property.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<Map<String, dynamic>> fetchTasks({String? url}) async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('auth_token');
    if (token == null) throw Exception('No auth token found');

    final uri = url == null
        ? Uri.parse('$baseUrl/tasks/')
        : Uri.parse(url);

    final res = await http.get(
      uri,
      headers: {'Authorization': 'Token $token'},
    );
    if (res.statusCode != 200) {
      throw Exception('Failed to load tasks (${res.statusCode})');
    }
    final data = jsonDecode(res.body);
    List<Task> tasks;
    String? next;

    if (data is List) {
      tasks = data.map((e) => Task.fromJson(e as Map<String, dynamic>)).toList();
      next = null;
    } else {
      tasks = (data['results'] as List)
          .map((e) => Task.fromJson(e as Map<String, dynamic>))
          .toList();
      next = data['next'] as String?;
    }
    return {'results': tasks, 'next': next};
  }

  Future<bool> createTask(Map<String, dynamic> payload) async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('auth_token');
    if (token == null) throw Exception('No auth token found');

    final res = await http.post(
      Uri.parse('$baseUrl/tasks/'),
      headers: {
        'Authorization': 'Token $token',
        'Content-Type': 'application/json',
      },
      body: jsonEncode(payload),
    );
    return res.statusCode == 201 || res.statusCode == 200;
  }

  Future<bool> updateTask(int id, Map<String, dynamic> payload) async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('auth_token');
    if (token == null) throw Exception('No auth token found');

    final res = await http.patch(
      Uri.parse('$baseUrl/tasks/$id/'),
      headers: {
        'Authorization': 'Token $token',
        'Content-Type': 'application/json',
      },
      body: jsonEncode(payload),
    );
    return res.statusCode == 200;
  }

  Future<bool> deleteTask(int id) async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('auth_token');
    if (token == null) throw Exception('No auth token found');

    final res = await http.delete(
      Uri.parse('$baseUrl/tasks/$id/'),
      headers: {'Authorization': 'Token $token'},
    );
    return res.statusCode == 204;
  }
}