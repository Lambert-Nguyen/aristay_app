import 'package:flutter/material.dart';

class StatusPill extends StatelessWidget {
  const StatusPill(this.status, {super.key});
  final String status;

  static const _bases = {
    'pending'     : Color(0xFFFFC107), // amber
    'in-progress' : Color(0xFF64B5F6), // blue 300
    'completed'   : Color(0xFF81C784), // green 300
    'canceled'    : Color(0xFFE57373), // red 300
  };

  @override
  Widget build(BuildContext context) {
    final base   = _bases[status] ?? const Color(0xFFB0BEC5);
    final scheme = Theme.of(context).colorScheme;
    final isDark = scheme.brightness == Brightness.dark;

    final bg     = isDark ? base.withValues(alpha: .18) : base.withValues(alpha: .20);
    final border = isDark ? base.withValues(alpha: .55) : base.withValues(alpha: .35);
    final label  = isDark ? base : base.withValues(alpha: .95);

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: border),
      ),
      child: Text(
        status.replaceAll('-', ' '),
        style: TextStyle(
          color: label,
          fontWeight: FontWeight.w700,
          fontSize: 12.5,
          height: 1.1,
        ),
      ),
    );
  }
}