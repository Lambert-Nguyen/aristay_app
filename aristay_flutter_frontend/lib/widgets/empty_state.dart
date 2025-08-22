import 'package:flutter/material.dart';
import 'package:flutter/services.dart' show rootBundle;

class EmptyState extends StatelessWidget {
  final String title;
  final String message;
  final String? illustrationAsset;        // e.g. assets/illustrations/empty_tasks.png
  final IconData? fallbackIcon;           // e.g. Icons.inbox
  final String? primaryActionLabel;
  final VoidCallback? onPrimaryAction;
  final String? secondaryActionLabel;
  final VoidCallback? onSecondaryAction;

  const EmptyState({
    super.key,
    required this.title,
    required this.message,
    this.illustrationAsset,
    this.fallbackIcon,
    this.primaryActionLabel,
    this.onPrimaryAction,
    this.secondaryActionLabel,
    this.onSecondaryAction,
  });

  Future<bool> _assetExists(String path) async {
    try {
      await rootBundle.load(path);
      return true;
    } catch (_) {
      return false;
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Center(
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        physics: const AlwaysScrollableScrollPhysics(),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            if (illustrationAsset != null)
              FutureBuilder<bool>(
                future: _assetExists(illustrationAsset!),
                builder: (_, snap) {
                  if (snap.connectionState != ConnectionState.done) {
                    return const SizedBox(height: 160); // reserve space
                  }
                  if (snap.data == true) {
                    final isSvg = illustrationAsset!.toLowerCase().endsWith('.svg');
                    if (isSvg) {
                      // If you later add flutter_svg, you can swap this block:
                      // return SvgPicture.asset(illustrationAsset!, height: 160);
                      return Icon(fallbackIcon ?? Icons.insert_photo, size: 96, color: Colors.grey[400]);
                    }
                    return Image.asset(illustrationAsset!, height: 160, fit: BoxFit.contain);
                  }
                  // fallback icon if asset not found
                  return Icon(fallbackIcon ?? Icons.insert_photo, size: 96, color: Colors.grey[400]);
                },
              )
            else
              Icon(fallbackIcon ?? Icons.insert_photo, size: 96, color: Colors.grey[400]),

            const SizedBox(height: 16),
            Text(title, style: theme.textTheme.titleLarge?.copyWith(fontWeight: FontWeight.bold)),
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