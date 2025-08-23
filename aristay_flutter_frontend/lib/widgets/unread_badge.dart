// lib/widgets/unread_badge.dart
import 'package:flutter/material.dart';

final ValueNotifier<int> unreadCount = ValueNotifier<int>(0);

class UnreadBadge extends StatelessWidget {
  final Widget icon;
  final VoidCallback? onTap;
  const UnreadBadge({required this.icon, this.onTap, super.key});

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<int>(
      valueListenable: unreadCount,
      builder: (_, count, __) {
        return Stack(
          clipBehavior: Clip.none,
          children: [
            IconButton(
              icon: icon,
              tooltip: 'Notifications',
              onPressed: onTap,
            ),
            Positioned(
              right: 4,
              top: 4,
              child: AnimatedSwitcher(
                duration: const Duration(milliseconds: 200),
                transitionBuilder: (child, anim) =>
                    ScaleTransition(scale: anim, child: child),
                child: count > 0
                    ? Container(
                        key: ValueKey(count),
                        padding: const EdgeInsets.all(2),
                        decoration: BoxDecoration(
                          color: Colors.red,
                          borderRadius: BorderRadius.circular(10),
                        ),
                        constraints: const BoxConstraints(minWidth: 16, minHeight: 16),
                        child: Text(
                          count > 99 ? '99+' : '$count',
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 10,
                            fontWeight: FontWeight.bold,
                          ),
                          textAlign: TextAlign.center,
                        ),
                      )
                    : const SizedBox.shrink(),
              ),
            ),
          ],
        );
      },
    );
  }
}