import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

/// Typed HTTP error you can reuse everywhere.
class ApiException implements Exception {
  final int statusCode;
  final String? detail;   // raw detail from server if present
  final String endpoint;  // best-effort; helps with logging
  ApiException({required this.statusCode, this.detail, required this.endpoint});

  @override
  String toString() => 'ApiException($statusCode) @ $endpoint: ${detail ?? ""}';
}

/// Try to extract "detail" or first error message from response JSON.
String? _extractDetail(String body) {
  try {
    final json = jsonDecode(body);
    if (json is Map<String, dynamic>) {
      if (json['detail'] is String) return json['detail'] as String;
      // If it's a dict of field errors, join the first ones
      final parts = <String>[];
      json.forEach((k, v) {
        if (v is List) parts.add(v.join(' '));
        else if (v is String) parts.add(v);
      });
      if (parts.isNotEmpty) return parts.join(' ');
    } else if (json is List && json.isNotEmpty) {
      final first = json.first;
      if (first is String) return first;
    }
  } catch (_) {}
  return null;
}

/// Create ApiException from http.Response
ApiException apiExceptionFromResponse(http.Response res) {
  final msg = _extractDetail(res.body);
  return ApiException(
    statusCode: res.statusCode,
    detail: msg,
    endpoint: res.request?.url.toString() ?? '(unknown)',
  );
}

/// One place to translate status codes to human text.
/// The [action] gets interpolated like "create a property".
String friendlyMessage(ApiException e, {String? action}) {
  final act = action ?? 'perform this action';
  switch (e.statusCode) {
    case 400: return e.detail ?? 'There’s a problem with the data you entered.';
    case 401: return 'Your session has expired. Please sign in again.';
    case 403: return "You don’t have permission to $act. Ask an administrator if you need access.";
    case 404: return e.detail ?? 'Not found. It may have been deleted, or you might not have access.';
    case 409: return e.detail ?? 'That conflicts with an existing record.';
    case 413: return 'The upload is too large.';
    case 429: return 'Too many requests. Please try again in a moment.';
    case 500:
    case 502:
    case 503:
    case 504: return 'Server error. Please try again shortly.';
    default:  return e.detail ?? 'Request failed (code ${e.statusCode}).';
  }
}

/// Show a SnackBar for any error (ApiException or otherwise).
void showFriendlyError(BuildContext context, Object err, {String? action}) {
  final msg = err is ApiException
      ? friendlyMessage(err, action: action)
      : (err is FormatException ? 'Unexpected response from server.' : err.toString());
  ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg)));
}