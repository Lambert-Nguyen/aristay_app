// lib/theme/app_theme.dart
import 'package:flutter/material.dart';

class AppTheme {
  static const _brand     = Color(0xFF0E4B8F);
  static const _brandDark = Color(0xFF0B3A6F);

  static ThemeData get light {
    final scheme = ColorScheme.fromSeed(
      seedColor: _brand,
      brightness: Brightness.light,
    );
    final base   = ThemeData(useMaterial3: true, colorScheme: scheme);

    return base.copyWith(
      scaffoldBackgroundColor: const Color(0xFFF8FAFD),
      appBarTheme: const AppBarTheme(centerTitle: false, elevation: 0),
      cardTheme: CardTheme(
        elevation: 0,
        surfaceTintColor: Colors.transparent,
        color: scheme.surface,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      ),
      inputDecorationTheme: const InputDecorationTheme(
        border: OutlineInputBorder(borderRadius: BorderRadius.all(Radius.circular(12))),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          side: const BorderSide(color: Colors.black12),
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
        ),
      ),
      chipTheme: ChipThemeData(
        shape: const StadiumBorder(),
        side: BorderSide(color: scheme.outlineVariant),
        labelStyle: TextStyle(color: scheme.onSurface),
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      ),

      // 👇 NEW: make ListTile styles explicit & with inherit:false
      listTileTheme: ListTileThemeData(
        iconColor: scheme.onSurfaceVariant,
        titleTextStyle: base.textTheme.titleMedium!.copyWith(
          inherit: false, // important: matches default
          color: scheme.onSurface,
          fontWeight: FontWeight.w700,
          fontSize: 16.5,
        ),
        subtitleTextStyle: base.textTheme.bodySmall!.copyWith(
          inherit: false, // important
          color: scheme.onSurface.withValues(alpha: .72),
          fontSize: 13,
        ),
      ),

      snackBarTheme: const SnackBarThemeData(behavior: SnackBarBehavior.floating),
      progressIndicatorTheme: const ProgressIndicatorThemeData(strokeWidth: 3),
      dividerTheme: const DividerThemeData(thickness: 1, space: 24),
      pageTransitionsTheme: const PageTransitionsTheme(
        builders: {
          TargetPlatform.iOS: CupertinoPageTransitionsBuilder(),
          TargetPlatform.android: FadeUpwardsPageTransitionsBuilder(),
          TargetPlatform.macOS: CupertinoPageTransitionsBuilder(),
        },
      ),
    );
  }

  static ThemeData get dark {
    final base = ThemeData(
      useMaterial3: true,
      colorScheme: ColorScheme.fromSeed(
        seedColor: _brandDark,
        brightness: Brightness.dark,
      ).copyWith(
        surface: const Color(0xFF151922),
        surfaceContainerLow: const Color(0xFF171C26),
        surfaceContainerHigh: const Color(0xFF1D2330),
        onSurface: const Color(0xFFEFF3F8),
        onSurfaceVariant: const Color(0xFFCAD2E2),
        outline: const Color(0xFF3B4456),
        outlineVariant: const Color(0xFF2A3141),
        primary: const Color(0xFF74A9FF),
      ),
    );

    final scheme = base.colorScheme;

    return base.copyWith(
      scaffoldBackgroundColor: const Color(0xFF0F141C),
      appBarTheme: const AppBarTheme(centerTitle: false, elevation: 0),
      cardTheme: CardTheme(
        elevation: 1,
        surfaceTintColor: Colors.transparent,
        color: scheme.surfaceContainerHigh,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      ),
      chipTheme: ChipThemeData(
        shape: const StadiumBorder(),
        side: BorderSide(color: scheme.outlineVariant),
        labelStyle: TextStyle(color: scheme.onSurface),
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
        selectedColor: scheme.primary.withValues(alpha: .14),
        backgroundColor: scheme.surfaceContainerLow,
      ),

      // 👇 Match light theme: inherit:false + same fields
      listTileTheme: ListTileThemeData(
        iconColor: scheme.onSurfaceVariant,
        titleTextStyle: base.textTheme.titleMedium!.copyWith(
          inherit: false,
          color: scheme.onSurface,
          fontWeight: FontWeight.w700,
          fontSize: 16.5,
        ),
        subtitleTextStyle: base.textTheme.bodySmall!.copyWith(
          inherit: false,
          color: scheme.onSurface.withValues(alpha: .72),
          fontSize: 13,
        ),
      ),

      snackBarTheme: const SnackBarThemeData(behavior: SnackBarBehavior.floating),
      progressIndicatorTheme: const ProgressIndicatorThemeData(strokeWidth: 3),
      dividerTheme: const DividerThemeData(thickness: 1, space: 24),
    );
  }
}