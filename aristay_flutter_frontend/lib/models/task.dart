class Task {
  final int    id;
  final String status;
  final String propertyName;
  final String? createdBy;
  final String? assignedTo;

  // plus any other fields you need (createdBy, assignedTo, etc.)

  Task({
    required this.id,
    required this.status,
    required this.propertyName,
    this.createdBy,
    this.assignedTo,
  });

  factory Task.fromJson(Map<String, dynamic> json) {
    // Try the flat property_name field first
    final rawPropName = json['property_name'];
    String name;
    if (rawPropName is String && rawPropName.isNotEmpty) {
      name = rawPropName;
    } else if (json['property'] is Map<String, dynamic> &&
        (json['property']['name'] as String?)?.isNotEmpty == true) {
      name = json['property']['name'] as String;
    } else {
      name = 'Unnamed';
    }

    // Safely parse status, default to 'unknown'
    final rawStatus = json['status'];
    final status = (rawStatus is String && rawStatus.isNotEmpty) ? rawStatus : 'unknown';

    String? createdByValue;
    final rawCreated = json['created_by'];
    if (rawCreated is String) {
      createdByValue = rawCreated;
    } else if (rawCreated != null) {
      createdByValue = rawCreated.toString();
    }


    return Task(
      id: json['id'] as int,
      status: status,
      propertyName: name,
      createdBy: createdByValue,
    );
  }

  /// Converts this Task instance back into a JSON-compatible map.
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'status': status,
      'property_name': propertyName,
      'created_by': createdBy,
      'assigned_to': assignedTo,
    };
  }
}