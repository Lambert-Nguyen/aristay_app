class User {
  final int id;
  final String username;
  final String? email;
  final String? firstName;
  final String? lastName;
  final bool isStaff;
  final bool isActive;
  final bool isSuperuser; 
  final String role;      
  final String timezone;

  User({
    required this.id,
    required this.username,
    this.email,
    this.firstName = '',
    this.lastName  = '',
    this.isStaff = false,
    this.isActive = true,
    this.isSuperuser = false,
    this.role = 'staff',
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
    isSuperuser: json['is_superuser'] as bool? ?? false, // ← ADD
    role: json['role'] as String? ?? 'staff',            // ← ADD
    timezone: json['timezone'] as String? ?? 'UTC',
  );

  User copyWith({bool? isStaff, bool? isActive, bool? isSuperuser, String? role}) => User(
    id: id,
    username: username,
    email: email,
    firstName: firstName,
    lastName: lastName,
    isStaff: isStaff ?? this.isStaff,
    isActive: isActive ?? this.isActive,
    isSuperuser: isSuperuser ?? this.isSuperuser,
    role: role ?? this.role,
    timezone: timezone,
  );
}