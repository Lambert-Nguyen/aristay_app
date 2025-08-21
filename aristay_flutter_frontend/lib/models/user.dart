class User {
  final int id;
  final String username;
  final String? email;
  final String firstName;
  final String lastName;
  final bool isStaff;
  final String timezone;

  User({
    required this.id,
    required this.username,
    this.email,
    this.firstName = '',
    this.lastName  = '',
    this.isStaff = false,
    this.timezone = 'UTC',
  });

  factory User.fromJson(Map<String, dynamic> json) => User(
        id: json['id'] as int,
        username: json['username'] as String,
        email: json['email'] as String?,
        firstName: json['first_name'] as String? ?? '',
        lastName: json['last_name'] as String? ?? '',
        isStaff: json['is_staff'] as bool? ?? false,
        timezone: json['timezone'] as String? ?? 'UTC',
      );
}