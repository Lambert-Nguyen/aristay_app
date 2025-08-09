// lib/models/notification.dart
class AppNotification {
  final int id;
  final int taskId;
  final String taskTitle;
  final String verb;
  final bool read;
  final DateTime timestamp;
  final DateTime? readAt;

  AppNotification({
    required this.id,
    required this.taskId,
    required this.taskTitle,
    required this.verb,
    required this.read,
    required this.timestamp,
    this.readAt,
  });

  factory AppNotification.fromJson(Map<String, dynamic> j) {
    return AppNotification(
      id:          j['id'],
      taskId:      j['task'],
      taskTitle:   j['task_title'] ?? '',
      verb:        j['verb'],
      read:        j['read'] as bool,
      timestamp:   DateTime.parse(j['timestamp']),
      readAt:      j['read_at'] != null ? DateTime.parse(j['read_at']) : null,
    );
  }
}