import 'dart:convert';
import 'dart:io';
import 'dart:math';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../models/property.dart';
import '../models/task.dart';
import '../models/user.dart';
import '../models/notification.dart';

/// Throws when the server returns a 400 with field‐level errors.
class ValidationException implements Exception {
  final Map<String, String> errors;
  ValidationException(this.errors);
}

class ApiService {
  // static const String baseUrl = 'http://127.0.0.1:8000/api';
  static const String baseUrl = 'http://192.168.1.40:8000/api';

  // ─────────────  Task mute / un-mute  ─────────────
  Future<bool> _postMute(int id, { required bool mute }) async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('auth_token')!;
    final uri   = Uri.parse('$baseUrl/tasks/$id/${mute ? "mute" : "unmute"}/');

    final res = await http.post(uri, headers: {
      'Authorization': 'Token $token',
      'Content-Type' : 'application/json',
    });

    if (res.statusCode != 200) return false;

    try {
      final obj = jsonDecode(res.body) as Map<String, dynamic>;
      // backend returns { "muted": true/false }
      return (obj['muted'] == true) == mute; // sanity check
    } catch (_) {
      return true; // keep previous behavior if parsing fails
    }
  }

  Future<bool> muteTask  (int id) => _postMute(id, mute: true);
  Future<bool> unmuteTask(int id) => _postMute(id, mute: false);

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
    bool? overdue,              // ← NEW
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
      if (search?.isNotEmpty == true)  qs['search']          = search!;
      if (property != null)             qs['property']        = '$property';
      if (status?.isNotEmpty == true)   qs['status']          = status!;
      if (assignedTo != null)           qs['assigned_to']     = '$assignedTo';
      if (dateFrom != null)             qs['created_at__gte'] = dateFrom.toIso8601String();
      if (dateTo   != null)             qs['created_at__lte'] = dateTo.toIso8601String();
      if (overdue == true)              qs['overdue']         = 'true';      // ← NEW

      uri = Uri.parse('$baseUrl/tasks/').replace(queryParameters: qs);
    }

    print('fetchTasks → $uri');
    final res = await http.get(uri, headers: {'Authorization': 'Token $token'});
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

    return {
      'results': tasks,
      'next'   : data is Map<String, dynamic> ? data['next'] as String? : null,
      'count'  : data is Map<String, dynamic> && data['count'] is int 
                   ? data['count'] as int 
                   : tasks.length,
    };
  }
  
  // Update the current user's profile (timezone, email, first/last name).
  Future<User> updateCurrentUser({
    String? timezone,
    String? email,
    String? firstName,
    String? lastName,
  }) async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('auth_token')!;
    final uri   = Uri.parse('$baseUrl/users/me/');

    final body = <String, dynamic>{};
    if (timezone != null) body['timezone']   = timezone;   // serializer maps to profile.timezone
    if (email    != null) body['email']      = email;
    if (firstName!= null) body['first_name'] = firstName;
    if (lastName != null) body['last_name']  = lastName;
    if (body.isEmpty) throw Exception('Nothing to update');

    final res = await http.patch(
      uri,
      headers: {'Authorization': 'Token $token','Content-Type':'application/json'},
      body: jsonEncode(body),
    );

    if (res.statusCode != 200) {
      throw Exception('Failed to update user (${res.statusCode}): ${res.body}');
    }

    return User.fromJson(jsonDecode(res.body) as Map<String, dynamic>);
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
    print('fetchUsers → $uri');
    final res = await http.get(uri, headers: {'Authorization': 'Token $token'});
    if (res.statusCode != 200) throw Exception('Failed to load users');

    final data  = jsonDecode(res.body) as Map<String, dynamic>;
    final raw   = data['results'] as List<dynamic>;
    final users = raw.map((e) => User.fromJson(e as Map<String, dynamic>)).toList();

    return {
      'results': users,
      'next':    data['next'] as String?,
      'count':   (data['count'] as int?) ?? users.length, // ← NEW
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

  /// Registers (or updates) the device’s FCM token with the backend.
  Future<void> _registerDeviceTokenOnce(String token) async {
    final prefs = await SharedPreferences.getInstance();
    final auth  = prefs.getString('auth_token');
    if (auth == null) throw Exception('No auth token saved');

    final res = await http.post(
      Uri.parse('$baseUrl/devices/'),
      headers: {
        'Authorization': 'Token $auth',
        'Content-Type'  : 'application/json',
      },
      body: jsonEncode({'token': token}),
    );

    if (res.statusCode != 200 && res.statusCode != 201) {
      throw Exception('Failed to register device token (${res.statusCode}): ${res.body}');
    }
  }

  /// Same as [_registerDeviceTokenOnce] but retries 3× with 2/4/8 s back-off (+ jitter).
  Future<void> registerDeviceTokenWithRetry(String token) async {
    const delays = [2, 4, 8]; // seconds
    for (var i = 0; i < delays.length; i++) {
      try {
        await _registerDeviceTokenOnce(token);
        return; // ✅ success
      } catch (e) {
        if (i == delays.length - 1) rethrow;     // give up
        final jitter = Random().nextInt(500); /* ms */ 
        await Future.delayed(Duration(
          milliseconds: delays[i] * 1000 + jitter));
      }
    }
  }

  /// Marks a notification as read.
  Future<void> markNotificationAsRead(String id) async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('auth_token')!;
    final res = await http.patch(
      Uri.parse('$baseUrl/notifications/$id/read/'),
      headers: {
        'Authorization': 'Token $token',
        'Content-Type': 'application/json',
      },
    );
    if (res.statusCode != 200) {
      throw Exception('Failed to mark notification $id as read (${res.statusCode})');
    }
  }

  // =============  🔔 NOTIFICATIONS  =============
  Future<Map<String, dynamic>> fetchNotifications({
    String? url,
    bool unreadOnly = false,
  }) async {
    final prefs  = await SharedPreferences.getInstance();
    final token  = prefs.getString('auth_token')!;
    final uri    = url != null
        ? Uri.parse(url)
        : Uri.parse('$baseUrl/notifications/')
            .replace(queryParameters: unreadOnly ? {'read': 'false'} : null);

    final res = await http.get(uri, headers: {'Authorization': 'Token $token'});
    if (res.statusCode != 200) {
      throw Exception('Failed to load notifications (${res.statusCode})');
    }

    final data = jsonDecode(res.body) as Map<String, dynamic>;
    return {
      'results':
          (data['results'] as List).map((e) => AppNotification.fromJson(e)).toList(),
      'next': data['next'] as String?,
      'count': data['count'] as int,
    };
  }

  Future<void> markNotificationRead(int id) async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('auth_token')!;
    final res = await http.patch(
      Uri.parse('$baseUrl/notifications/$id/read/'),
      headers: {'Authorization': 'Token $token'},
    );
    if (res.statusCode != 200) {
      throw Exception('Failed to mark notification read (${res.statusCode})');
    }
  }

  Future<void> markAllNotificationsRead() async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('auth_token')!;
    final res = await http.post(
      Uri.parse('$baseUrl/notifications/mark-all-read/'),
      headers: {'Authorization': 'Token $token'},
    );
    if (res.statusCode != 200) {
      throw Exception('Failed to mark all notifications read (${res.statusCode})');
    }
  }
}