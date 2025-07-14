import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../models/property.dart';
import '../models/task.dart';
import '../models/user.dart';

class ApiService {
  static const String baseUrl = 'http://127.0.0.1:8000/api';

  Future<List<Property>> fetchProperties() async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('auth_token')!;
    final res = await http.get(
      Uri.parse('$baseUrl/properties/'),
      headers: {'Authorization': 'Token $token'},
    );
    if (res.statusCode != 200) throw Exception('Failed to load properties');
    final body = jsonDecode(res.body);
    final raw = body is List
        ? body
        : body is Map<String, dynamic> && body['results'] is List
            ? body['results']
            : throw Exception('Unexpected properties payload');
    return (raw as List)
        .map((e) => Property.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<bool> createProperty(Map<String, dynamic> payload) async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('auth_token')!;
    final res = await http.post(
      Uri.parse('$baseUrl/properties/'),
      headers: {
        'Authorization': 'Token $token',
        'Content-Type': 'application/json',
      },
      body: jsonEncode(payload),
    );
    return res.statusCode == 201;
  }

  Future<bool> updateProperty(int id, Map<String, dynamic> payload) async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('auth_token')!;
    final res = await http.patch(
      Uri.parse('$baseUrl/properties/$id/'),
      headers: {
        'Authorization': 'Token $token',
        'Content-Type': 'application/json',
      },
      body: jsonEncode(payload),
    );
    return res.statusCode == 200;
  }

  Future<bool> deleteProperty(int id) async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('auth_token')!;
    final res = await http.delete(
      Uri.parse('$baseUrl/properties/$id/'),
      headers: {'Authorization': 'Token $token'},
    );
    return res.statusCode == 204;
  }

  Future<bool> uploadTaskImage(int taskId, File imageFile) async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('auth_token')!;
    final uri = Uri.parse('$baseUrl/tasks/$taskId/images/');
    final request = http.MultipartRequest('POST', uri)
      ..headers['Authorization'] = 'Token $token'
      ..files.add(await http.MultipartFile.fromPath('image', imageFile.path));
    final resp = await request.send();
    return resp.statusCode == 201;
  }

  Future<Map<String, dynamic>> createTask(Map<String, dynamic> payload) async {
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
    if (res.statusCode == 201 || res.statusCode == 200) {
      return jsonDecode(res.body) as Map<String, dynamic>;
    } else {
      throw Exception('Failed to create task (${res.statusCode})');
    }
  }

  Future<bool> updateTask(int id, Map<String, dynamic> payload) async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('auth_token')!;
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
    final token = prefs.getString('auth_token')!;
    final res = await http.delete(
      Uri.parse('$baseUrl/tasks/$id/'),
      headers: {'Authorization': 'Token $token'},
    );
    return res.statusCode == 204;
  }

  Future<Task> fetchTask(int id) async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('auth_token')!;
    final res = await http.get(
      Uri.parse('$baseUrl/tasks/$id/'),
      headers: {'Authorization': 'Token $token'},
    );
    if (res.statusCode != 200) throw Exception('Failed to load task');
    return Task.fromJson(jsonDecode(res.body) as Map<String, dynamic>);
  }

  Future<Map<String, dynamic>> fetchTasks({String? url}) async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('auth_token')!;
    final uri = Uri.parse(url ?? '$baseUrl/tasks/');
    final res = await http.get(
      uri,
      headers: {'Authorization': 'Token $token'},
    );
    if (res.statusCode != 200) throw Exception('Failed to load tasks');
    final data = jsonDecode(res.body);
    final raw = data is List
        ? data
        : data is Map<String, dynamic> && data['results'] is List
            ? data['results']
            : throw Exception('Unexpected tasks payload');
    final tasks = (raw as List)
        .map((e) => Task.fromJson(e as Map<String, dynamic>))
        .toList();
    return {
      'results': tasks,
      'next': data is Map<String, dynamic> ? data['next'] as String? : null,
    };
  }

  Future<List<User>> fetchUsers() async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('auth_token')!;
    final res = await http.get(
      Uri.parse('$baseUrl/users/'),
      headers: {'Authorization': 'Token $token'},
    );
    if (res.statusCode != 200) throw Exception('Failed to load users');

    final data = jsonDecode(res.body);
    final raw = data is List
        ? data
        : data is Map<String, dynamic> && data['results'] is List
            ? data['results']
            : throw Exception('Unexpected users payload');
    return (raw as List)
        .map((e) => User.fromJson(e as Map<String, dynamic>))
        .toList();
  }
}
