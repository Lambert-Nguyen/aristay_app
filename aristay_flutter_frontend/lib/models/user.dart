class User {
  final int id;
  final String username;
  final String? email;
  final String? firstName;   // make nullable to match usage
  final String? lastName;
  final bool isStaff;
  final bool isActive;
  final String timezone;

  User({
    required this.id,
    required this.username,
    this.email,
    this.firstName = '',
    this.lastName  = '',
    this.isStaff = false,
    this.isActive = true,
    this.timezone = 'UTC',
  });

  factory User.fromJson(Map<String, dynamic> json) => User(
        id: json['id'] as int,
        username: json['username'] as String,
        email: json['email'] as String?,
        firstName: json['first_name'] as String? ?? '',
        lastName: json['last_name'] as String? ?? '',
        isStaff: json['is_staff'] as bool? ?? false,
        isActive: json['is_active'] as bool? ?? true,
        timezone: json['timezone'] as String? ?? 'UTC',
  );

  User copyWith({bool? isStaff, bool? isActive}) => User(
    id: id,
    username: username,
    email: email,
    firstName: firstName,
    lastName: lastName,
    isStaff: isStaff ?? this.isStaff,
    isActive: isActive ?? this.isActive,
    timezone: timezone,
  );
}