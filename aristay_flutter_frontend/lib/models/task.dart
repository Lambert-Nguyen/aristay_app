// lib/models/task.dart

class Task {
  final int     id;
  final int     propertyId;
  final String  propertyName;
  final String  taskType;
  final String  title;
  final String  description;
  final String  status;
  final String? createdBy;
  final String? assignedTo;       // now holds the username
  final String? modifiedBy;
  final List<String> history;
  final DateTime createdAt;
  final DateTime modifiedAt;

  Task({
    required this.id,
    required this.propertyId,
    required this.propertyName,
    required this.taskType,
    required this.title,
    required this.description,
    required this.status,
    this.createdBy,
    this.assignedTo,
    this.modifiedBy,
    required this.history,
    required this.createdAt,
    required this.modifiedAt,
  });

  factory Task.fromJson(Map<String, dynamic> json) {
    return Task(
      id:             json['id'] as int,
      propertyId:     json['property'] as int,
      propertyName:   (json['property_name'] as String?) ?? 'Unnamed',
      taskType:       (json['task_type'] as String?)      ?? '',
      title:          (json['title'] as String?)          ?? '',
      description:    (json['description'] as String?)    ?? '',
      status:         (json['status'] as String?)         ?? '',
      createdBy:      json['created_by'] as String?,
      assignedTo:     json['assigned_to_username'] as String?,
      modifiedBy:     json['modified_by'] as String?,
      history:        (json['history'] as List<dynamic>?)
                         ?.map((e) => e.toString())
                         .toList()                       ?? [],
      createdAt:      DateTime.parse(json['created_at']   as String),
      modifiedAt:     DateTime.parse(json['modified_at']  as String),
    );
  }

  Map<String, dynamic> toJson() => {
    'id':                 id,
    'property':           propertyId,
    'task_type':          taskType,
    'title':              title,
    'description':        description,
    'status':             status,
    // only writing properties you actually allow to change…
  };
}