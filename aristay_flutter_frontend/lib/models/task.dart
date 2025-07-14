// lib/models/task.dart

class Task {
  final int    id;
  final int    propertyId;
  final String propertyName;
  final String taskType;
  final String title;
  final String description;
  final String status;
  final String? createdBy;
  final int?    assignedToId;
  final String? assignedToUsername;
  final String? modifiedBy;
  final List<String> history;
  final List<String> imageUrls;
  final List<int>    imageIds;       // ← new!

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
    this.history = const [],
    required this.createdAt, 
    required this.modifiedAt,
    this.imageUrls = const [],
    this.imageIds      = const [],    // ← new!
  });

  factory Task.fromJson(Map<String, dynamic> json) {
    // property name (nested or flat)
    String name;
    final rawProp = json['property_name'];
    if (rawProp is String && rawProp.isNotEmpty) {
      name = rawProp;
    } else if (json['property'] is Map<String, dynamic>) {
      name = (json['property']['name'] as String?) ?? 'Unnamed';
    } else {
      name = 'Unnamed';
    }

    // status
    final rawStatus = json['status'];
    final status = (rawStatus is String && rawStatus.isNotEmpty)
        ? rawStatus
        : 'unknown';

    // createdBy username
    String? createdBy;
    if (json['created_by'] != null) {
      createdBy = json['created_by'].toString();
    }

    // assigned_to (id) and assigned_to_username
    int? assignedId;
    if (json['assigned_to'] is int) {
      assignedId = json['assigned_to'] as int;
    }
    String? assignedUsername;
    if (json['assigned_to_username'] != null) {
      assignedUsername = json['assigned_to_username'].toString();
    }

    // modifiedBy
    String? modifiedBy;
    if (json['modified_by_username'] != null) {
      modifiedBy = json['modified_by_username'] as String;
    } else if (json['modified_by'] != null) {
      modifiedBy = json['modified_by'].toString();
    }

    // history list
    List<String> history = [];
    if (json['history'] is List) {
      history = (json['history'] as List)
          .map((e) => e.toString())
          .toList();
    }
    // parse the timestamps:
    final createdAt = DateTime.parse(json['created_at'] as String);
    final modifiedAt = DateTime.parse(json['modified_at'] as String);
    // Build parallel lists for image URLs and IDs:
    final urls = <String>[];
    final ids  = <int>[];

    if (json['images'] is List) {
      for (final item in (json['images'] as List<dynamic>)) {
        if (item is Map<String, dynamic>) {
          // Serializer puts { id, image: URL, uploaded_at }
          final url = item['image'] as String?;
          final id  = item['id']   as int?;
          if (url != null && id != null) {
            urls.add(url);
            ids.add(id);
          }
        }
      }
    }

    return Task(
      id:                    json['id'] as int,
      propertyId:            json['property'] is int
          ? json['property'] as int
          : int.parse(json['property'].toString()),
      propertyName:          name,
      taskType:              (json['task_type'] as String?) ?? 'cleaning',
      title:                 (json['title'] as String?)     ?? '',
      description:           (json['description'] as String?) ?? '',
      status:                status,
      createdBy:             createdBy,
      assignedToId:          assignedId,
      assignedToUsername:    assignedUsername,
      modifiedBy:            modifiedBy,
      history:               history,
      createdAt:             DateTime.parse(json['created_at'] as String),
      modifiedAt:            DateTime.parse(json['modified_at'] as String),
      imageUrls:             urls,     // ← new
      imageIds:              ids,      // ← new
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id':                    id,
      'property':              propertyId,
      'task_type':             taskType,
      'title':                 title,
      'description':           description,
      'status':                status,
      'assigned_to':           assignedToId,
      // if you need to send back history or modified_by you can add here
    };
  }
}