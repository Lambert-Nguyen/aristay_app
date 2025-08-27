class Property {
  final int id;          // database PK used in /properties/{id}/
  final String name;     // display name (can be "5", "TEST", etc.)
  final int? number;     // optional business number/code

  Property({
    required this.id,
    required this.name,
    this.number
  });

  factory Property.fromJson(Map<String, dynamic> j) => Property(
    id: j['id'] as int,               // <- MUST be PK
    name: (j['name'] as String?) ?? '',
    number: j['number'] as int?,      // if your API has this
  );
}