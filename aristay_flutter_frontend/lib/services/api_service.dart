import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../models/property.dart';
import '../models/task.dart';
import '../models/user.dart';

/// Throws when the server returns a 400 with field‐level errors.
class ValidationException implements Exception {
  final Map<String, String> errors;
  ValidationException(this.errors);
}

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

  Future<void> uploadTaskImage(int taskId, File imageFile) async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('auth_token')!;
    final uri = Uri.parse('$baseUrl/tasks/$taskId/images/');
    final request = http.MultipartRequest('POST', uri)
      ..headers['Authorization'] = 'Token $token'
      ..files.add(await http.MultipartFile.fromPath('image', imageFile.path));

    final response = await request.send();
    final body = await response.stream.bytesToString();

    if (response.statusCode != 201) {
      String message;
      try {
        final json = jsonDecode(body);
        message = json['detail'] ?? body;
      } catch (_) {
        message = body;
      }
      throw Exception('Failed to upload photo: $message (code ${response.statusCode})');
    }
  }

  /// Creates a new task, or throws ValidationException on 400.
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
    }

    if (res.statusCode == 400) {
      final body = jsonDecode(res.body) as Map<String, dynamic>;
      final errors = <String, String>{};
      body.forEach((key, value) {
        if (value is List) {
          errors[key] = value.join(' ');
        } else {
          errors[key] = value.toString();
        }
      });
      throw ValidationException(errors);
    }

    throw Exception('Failed to create task (${res.statusCode})');
  }

  /// Updates an existing task, or throws ValidationException on 400.
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

    if (res.statusCode == 200) return true;

    if (res.statusCode == 400) {
      final body = jsonDecode(res.body) as Map<String, dynamic>;
      final errors = <String, String>{};
      body.forEach((key, value) {
        if (value is List) {
          errors[key] = value.join(' ');
        } else {
          errors[key] = value.toString();
        }
      });
      throw ValidationException(errors);
    }

    throw Exception('Failed to update task (${res.statusCode})');
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

  Future<void> deleteTaskImage(int taskId, int imageId) async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('auth_token')!;
    final res = await http.delete(
      Uri.parse('$baseUrl/tasks/$taskId/images/$imageId/'),
      headers: {'Authorization': 'Token $token'},
    );

    if (res.statusCode != 204) {
      String message;
      try {
        final body = jsonDecode(res.body);
        message = body['detail'] ?? res.body;
      } catch (_) {
        message = res.body;
      }
      throw Exception('Failed to delete photo: $message (code ${res.statusCode})');
    }
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