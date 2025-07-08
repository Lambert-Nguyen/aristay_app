import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../models/property.dart';
import '../models/task.dart';

class ApiService {
  // static const String baseUrl = 'http://192.168.1.41:8000/api';
  // static const String baseUrl = 'http://172.168.98.196:8000/api';
  static const String baseUrl = 'http://127.0.0.1:8000/api';

  /// Returns a Map with
  ///   "results": List<Task>
  ///   "next": String? (pagination)
  Future<Map<String, dynamic>> fetchTasks({String? url}) async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('auth_token');
    if (token == null) throw Exception('No auth token found');

    final uri = url == null
        ? Uri.parse('$baseUrl/tasks/')
        : Uri.parse(url);

    final response = await http.get(
      uri,
      headers: { 'Authorization': 'Token $token' },
    );
    if (response.statusCode != 200) {
      throw Exception('Failed to load tasks. Status code: ${response.statusCode}');
    }

    final jsonBody = jsonDecode(response.body);
    List<dynamic> rawList;
    if (jsonBody is List) {
      rawList = jsonBody;
    } else if (jsonBody is Map && jsonBody.containsKey('results')) {
      rawList = jsonBody['results'] as List<dynamic>;
    } else {
      rawList = [];
    }

    final tasks = rawList.map((e) => Task.fromJson(e as Map<String, dynamic>)).toList();
    final next = (jsonBody is Map && jsonBody.containsKey('next')) ? jsonBody['next'] as String? : null;

    return { 'results': tasks, 'next': next };
  }
    
    Future<bool> updateCleaningTask(int taskId, Map<String, dynamic> updatedData) async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('auth_token');
    if (token == null) {
      throw Exception('No auth token found');
    }

    final url = Uri.parse('$baseUrl/tasks/$taskId/');
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

  Future<bool> createTask(Map<String, dynamic> newData) async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('auth_token');
    if (token == null) throw Exception('No auth token found');
    final uri = Uri.parse('$baseUrl/tasks/');
    final response = await http.post(
      uri,
      headers: {
        'Authorization': 'Token $token',
        'Content-Type': 'application/json',
      },
      body: jsonEncode(newData),
    );
    return response.statusCode == 201 || response.statusCode == 200;
  }

  /// Fetches the list of properties from /api/properties/
  /// Returns a List<Property>.
  Future<List<Property>> fetchProperties() async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('auth_token');
    if (token == null) throw Exception('No auth token found');

    final uri = Uri.parse('$baseUrl/properties/');
    final response = await http.get(
      uri,
      headers: { 'Authorization': 'Token $token' },
    );

    if (response.statusCode != 200) {
      throw Exception('Failed to load properties (status ${response.statusCode})');
    }

    final decoded = jsonDecode(response.body);
    late final List<dynamic> rawList;

    if (decoded is List) {
      rawList = decoded;
    } else if (decoded is Map && decoded.containsKey('results')) {
      rawList = decoded['results'] as List<dynamic>;
    } else {
      throw Exception('Unexpected JSON structure for properties');
    }

    return rawList
        .map((e) => Property.fromJson(e as Map<String, dynamic>))
        .toList();
  }
}