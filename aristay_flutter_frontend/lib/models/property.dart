class Property {
  final int id;
  final String name;
  Property({required this.id, required this.name});
  factory Property.fromJson(Map<String, dynamic> json) => Property(
        id: json['id'] as int,
        name: json['name'] as String,
      );
}