class User {
  final int id;
  final String username;
  final String? email;
  final bool isStaff;

  User({
    required this.id,
    required this.username,
    this.email,
    this.isStaff = false,
  });

  factory User.fromJson(Map<String, dynamic> json) => User(
        id: json['id'] as int,
        username: json['username'] as String,
        email: json['email'] as String?,
        isStaff: json['is_staff'] as bool? ?? false,
      );
}