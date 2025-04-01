import 'package:http/http.dart' as http;
import 'dart:convert';

class ApiService {
  // Replace with your local IP address and port if needed.
  // For example, if your Django server is at 192.168.1.45:8000:
  static const String baseUrl = 'http://192.168.1.41:8000/api';

  Future<List<dynamic>?> fetchCleaningTasks() async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/cleaning-tasks/'));
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        print('Error: ${response.statusCode}');
        return null;
      }
    } catch (e) {
      print('Exception: $e');
      return null;
    }
  }
}
