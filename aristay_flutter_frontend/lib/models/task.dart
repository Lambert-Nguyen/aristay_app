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
  final int?    assignedToId;
  final String? assignedToUsername;
  final String? modifiedBy;
  final List<String> history;
  final List<String> imageUrls;
  final List<int>    imageIds;
  final bool         isMuted;

  // new fields:
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
    this.assignedToId,
    this.assignedToUsername,
    this.modifiedBy,
    this.history        = const [],
    required this.createdAt,
    required this.modifiedAt,
    this.imageUrls      = const [],
    this.imageIds       = const [],
    this.isMuted        = false,
  });

  Task copyWith({
    int? id,
    int? propertyId,
    String? propertyName,
    String? taskType,
    String? title,
    String? description,
    String? status,
    String? createdBy,
    int? assignedToId,
    String? assignedToUsername,
    String? modifiedBy,
    List<String>? history,
    List<String>? imageUrls,
    List<int>? imageIds,
    bool? isMuted,
    DateTime? createdAt,
    DateTime? modifiedAt,
  }) {
    return Task(
      id: id ?? this.id,
      propertyId: propertyId ?? this.propertyId,
      propertyName: propertyName ?? this.propertyName,
      taskType: taskType ?? this.taskType,
      title: title ?? this.title,
      description: description ?? this.description,
      status: status ?? this.status,
      createdBy: createdBy ?? this.createdBy,
      assignedToId: assignedToId ?? this.assignedToId,
      assignedToUsername: assignedToUsername ?? this.assignedToUsername,
      modifiedBy: modifiedBy ?? this.modifiedBy,
      history: history ?? this.history,
      imageUrls: imageUrls ?? this.imageUrls,
      imageIds: imageIds ?? this.imageIds,
      isMuted: isMuted ?? this.isMuted,
      createdAt: createdAt ?? this.createdAt,
      modifiedAt: modifiedAt ?? this.modifiedAt,
    );
  }


  factory Task.fromJson(Map<String, dynamic> json) {
    // parse the two timestamps once
    final createdAtStr  = json['created_at']  as String?;
    final modifiedAtStr = json['modified_at'] as String?;
    final createdAt  = createdAtStr  != null ? DateTime.parse(createdAtStr)  : DateTime.now().toUtc();
    final modifiedAt = modifiedAtStr != null ? DateTime.parse(modifiedAtStr) : createdAt;

    // build lists for images
    final urls = <String>[];
    final ids  = <int>[];
    if (json['images'] is List) {
      for (final item in (json['images'] as List<dynamic>)) {
        if (item is Map<String, dynamic>) {
          final url = item['image'] as String?;
          final id  = item['id']    as int?;
          if (url != null && id != null) {
            urls.add(url);
            ids.add(id);
          }
        }
      }
    }

    // flatten history
    final history = (json['history'] as List?)
            ?.map((e) => e.toString())
            .toList() 
          ?? <String>[];

    // property name
    String propName;
    final rawProp = json['property_name'];
    if (rawProp is String && rawProp.isNotEmpty) {
      propName = rawProp;
    } else if (json['property'] is Map<String, dynamic>) {
      propName = (json['property']['name'] as String?) ?? 'Unnamed';
    } else {
      propName = 'Unnamed';
    }

    return Task(
      id:                    json['id'] as int,
      propertyId:            json['property'] is int
                                ? json['property'] as int
                                : int.parse(json['property'].toString()),
      propertyName:          propName,
      taskType:              (json['task_type'] as String?) ?? 'cleaning',
      title:                 (json['title'] as String?)     ?? '',
      description:           (json['description'] as String?) ?? '',
      status:                (json['status'] as String?)    ?? '',
      createdBy:             json['created_by']?.toString(),
      assignedToId:          json['assigned_to'] is int
                                ? json['assigned_to'] as int
                                : null,
      assignedToUsername:    json['assigned_to_username']?.toString(),
      modifiedBy:            json['modified_by_username']?.toString()
                              ?? json['modified_by']?.toString(),
      history:               history,
      createdAt:             createdAt,
      modifiedAt:            modifiedAt,
      imageUrls:             urls,
      imageIds:              ids,
      isMuted:               (json['is_muted']  as bool?) ?? false,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'property':    propertyId,
      'task_type':   taskType,
      'title':       title,
      'description': description,
      'status':      status,
      'assigned_to': assignedToId,
      // note: isMuted is server-only
    };
  }
}