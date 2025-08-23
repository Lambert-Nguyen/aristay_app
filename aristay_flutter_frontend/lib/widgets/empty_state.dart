// lib/widgets/empty_state.dart (replace file contents)
import 'package:flutter/material.dart';

class EmptyState extends StatelessWidget {
  final String title;
  final String message;
  final String? illustrationAsset;    // e.g. assets/illustrations/empty_tasks.png
  final double illustrationHeight;
  final String? semanticsLabel;       // optional accessibility label
  final IconData? fallbackIcon;       // e.g. Icons.inbox
  final String? primaryActionLabel;
  final VoidCallback? onPrimaryAction;
  final String? secondaryActionLabel;
  final VoidCallback? onSecondaryAction;

  const EmptyState({
    super.key,
    required this.title,
    required this.message,
    this.illustrationAsset,
    this.illustrationHeight = 160,
    this.semanticsLabel,
    this.fallbackIcon,
    this.primaryActionLabel,
    this.onPrimaryAction,
    this.secondaryActionLabel,
    this.onSecondaryAction,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    Widget illustration() {
      if (illustrationAsset == null) {
        return Icon(fallbackIcon ?? Icons.insert_photo, size: 96, color: Colors.grey[400]);
      }
      final isSvg = illustrationAsset!.toLowerCase().endsWith('.svg');
      if (isSvg) {
        // If you later add flutter_svg, swap this with SvgPicture.asset(...)
        return Icon(fallbackIcon ?? Icons.insert_photo, size: 96, color: Colors.grey[400]);
      }
      return Image.asset(
        illustrationAsset!,
        height: illustrationHeight,
        fit: BoxFit.contain,
        errorBuilder: (_, __, ___) =>
            Icon(fallbackIcon ?? Icons.insert_photo, size: 96, color: Colors.grey[400]),
      );
    }

    return Center(
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        physics: const AlwaysScrollableScrollPhysics(),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Semantics(
              label: semanticsLabel ?? title,
              image: true,
              child: illustration(),
            ),
            const SizedBox(height: 16),
            Text(
              title,
              style: theme.textTheme.titleLarge?.copyWith(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            Text(
              message,
              style: theme.textTheme.bodyMedium?.copyWith(color: Colors.grey[600]),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 16),
            if (primaryActionLabel != null && onPrimaryAction != null)
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: onPrimaryAction,
                  child: Text(primaryActionLabel!),
                ),
              ),
            if (secondaryActionLabel != null && onSecondaryAction != null) ...[
              const SizedBox(height: 8),
              TextButton(
                onPressed: onSecondaryAction,
                child: Text(secondaryActionLabel!),
              ),
            ],
          ],
        ),
      ),
    );
  }
}