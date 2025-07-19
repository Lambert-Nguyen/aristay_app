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

    Future<Map<String, dynamic>> fetchTasks({
    String? url,
    String? search,
    int? property,
    String? status,
    int? assignedTo,
    DateTime? dateFrom,
    DateTime? dateTo,
  }) async {
    // 1) Load token
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('auth_token')!;
    
    // 2) Build or parse URI
    late final Uri uri;
    if (url != null) {
      uri = Uri.parse(url);
    } else {
      final qs = <String, String>{};
      if (search != null && search.isNotEmpty)        qs['search']            = search;
      if (property != null)                           qs['property']          = property.toString();
      if (status != null && status.isNotEmpty)        qs['status']            = status;
      if (assignedTo != null)                         qs['assigned_to']       = assignedTo.toString();
      if (dateFrom != null)                           qs['created_at__gte']   = dateFrom.toIso8601String();
      if (dateTo != null)                             qs['created_at__lte']   = dateTo.toIso8601String();
      
      uri = Uri.parse('$baseUrl/tasks/').replace(queryParameters: qs);
    }
    
    // 3) Debug print
    print('fetchTasks → $uri');
    
    // 4) GET request
    final res = await http.get(
      uri,
      headers: {'Authorization': 'Token $token'},
    );
    if (res.statusCode != 200) {
      throw Exception('Failed to load tasks (${res.statusCode})');
    }
    
    // 5) Decode payload
    final data = jsonDecode(res.body);
    final raw = data is List
        ? data
        : (data is Map<String, dynamic> && data['results'] is List)
            ? data['results']
            : throw Exception('Unexpected tasks payload');
    
    // 6) Map to Task models
    final tasks = (raw as List)
        .map((e) => Task.fromJson(e as Map<String, dynamic>))
        .toList();
    
    // 7) Return results + next URL (if paginated)
    final next = data is Map<String, dynamic> ? data['next'] as String? : null;
    final count = data is Map<String, dynamic> && data['count'] is int
        ? data['count'] as int
        : tasks.length;
    return {
      'results': tasks,
      'next'   : next,
      'count'  : count,
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

  Future<Map<String, dynamic>> fetchUsers({ String? url }) async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('auth_token')!;
    final uri = Uri.parse(url ?? '$baseUrl/users/');
    print('fetchUsers → $uri');            // ← add this to debug
    final res = await http.get(uri,
      headers: {'Authorization': 'Token $token'},
    );
    if (res.statusCode != 200) throw Exception('Failed to load users');

    final data = jsonDecode(res.body) as Map<String, dynamic>;
    final raw   = data['results'] as List<dynamic>;
    final users = raw
        .map((e) => User.fromJson(e as Map<String, dynamic>))
        .toList();
    return {
      'results': users,
      'next':    data['next'] as String?,
    };
  }
  
  /// Invites a new user (admin only). Throws ValidationException on 400.
  Future<void> inviteUser(String username, String email) async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('auth_token')!;
    final res = await http.post(
      Uri.parse('$baseUrl/admin/invite/'),
      headers: {
        'Authorization': 'Token $token',
        'Content-Type': 'application/json',
      },
      body: jsonEncode({'username': username, 'email': email}),
    );

    if (res.statusCode == 201) return;

    if (res.statusCode == 400) {
      final Map<String, dynamic> body = jsonDecode(res.body);
      final errors = <String, String>{};
      body.forEach((k, v) {
        errors[k] = (v is List) ? v.join(' ') : v.toString();
      });
      throw ValidationException(errors);
    }

    throw Exception('Invite failed (${res.statusCode}): ${res.body}');
  }

  /// Sends a password‐reset email (admin only).
  Future<void> resetUserPassword(String email) async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('auth_token')!;
    final res = await http.post(
      Uri.parse('$baseUrl/admin/reset-password/'),
      headers: {
        'Authorization': 'Token $token',
        'Content-Type': 'application/json',
      },
      body: jsonEncode({'email': email}),
    );

    if (res.statusCode == 200) return;

    if (res.statusCode == 400) {
      final Map<String, dynamic> body = jsonDecode(res.body);
      final errors = <String, String>{};
      body.forEach((k, v) {
        errors[k] = (v is List) ? v.join(' ') : v.toString();
      });
      throw ValidationException(errors);
    }

    throw Exception('Reset failed (${res.statusCode}): ${res.body}');
  }
  Future<User> fetchCurrentUser() async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('auth_token')!;
    final res = await http.get(
      Uri.parse('$baseUrl/users/me/'),
      headers: {'Authorization': 'Token $token'},
    );
    if (res.statusCode != 200) throw Exception('Failed to load current user');
    return User.fromJson(jsonDecode(res.body) as Map<String, dynamic>);
  }
  
  /// Admin: create a new user
  Future<void> createUser({
    required String username,
    required String email,
    required String password,
    required bool isStaff,
  }) async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('auth_token')!;
    final res = await http.post(
      Uri.parse('$baseUrl/admin/create-user/'),
      headers: {
        'Authorization': 'Token $token',
        'Content-Type': 'application/json',
      },
      body: jsonEncode({
        'username': username,
        'email': email,
        'password': password,
        'is_staff': isStaff,
      }),
    );
    if (res.statusCode == 201) return;

    if (res.statusCode == 400) {
      final body = jsonDecode(res.body) as Map<String, dynamic>;
      final errors = <String,String>{};
      body.forEach((k,v) {
        errors[k] = (v is List) ? v.join(' ') : v.toString();
      });
      throw ValidationException(errors);
    }

    throw Exception('Failed to create user (${res.statusCode})');
  }
  /// GET /api/tasks/count-by-status/
  Future<Map<String, dynamic>> fetchTaskCounts() async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('auth_token')!;
    final uri = Uri.parse('$baseUrl/tasks/count-by-status/');
    final res = await http.get(
      uri,
      headers: {'Authorization': 'Token $token'},
    );
    if (res.statusCode != 200) {
      throw Exception('Failed to load task counts (${res.statusCode})');
    }
    return jsonDecode(res.body) as Map<String, dynamic>;
  }
}