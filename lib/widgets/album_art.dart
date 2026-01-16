import 'dart:typed_data';
import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

class AlbumArt extends StatelessWidget {
  final Uint8List? albumArt;
  final String? albumArtPath;
  final double size;
  final double borderRadius;
  final bool showShadow;
  final IconData placeholderIcon;

  const AlbumArt({
    super.key,
    this.albumArt,
    this.albumArtPath,
    this.size = 56,
    this.borderRadius = 4,
    this.showShadow = false,
    this.placeholderIcon = Icons.music_note_rounded,
  });

  @override
  Widget build(BuildContext context) {
    Widget child;

    if (albumArt != null && albumArt!.isNotEmpty) {
      child = Image.memory(
        albumArt!,
        fit: BoxFit.cover,
        width: size,
        height: size,
        errorBuilder: (context, error, stackTrace) => _buildPlaceholder(),
      );
    } else {
      child = _buildPlaceholder();
    }

    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(borderRadius),
        boxShadow: showShadow
            ? [
                BoxShadow(
                  color: Colors.black.withOpacity(0.3),
                  blurRadius: 20,
                  offset: const Offset(0, 10),
                ),
              ]
            : null,
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(borderRadius),
        child: child,
      ),
    );
  }

  Widget _buildPlaceholder() {
    return Container(
      width: size,
      height: size,
      color: AppTheme.lightGrey,
      child: Icon(
        placeholderIcon,
        color: AppTheme.textGrey,
        size: size * 0.5,
      ),
    );
  }
}

class AlbumArtHero extends StatelessWidget {
  final Uint8List? albumArt;
  final String heroTag;
  final double size;
  final double borderRadius;

  const AlbumArtHero({
    super.key,
    this.albumArt,
    required this.heroTag,
    this.size = 300,
    this.borderRadius = 8,
  });

  @override
  Widget build(BuildContext context) {
    return Hero(
      tag: heroTag,
      child: Container(
        width: size,
        height: size,
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(borderRadius),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.4),
              blurRadius: 30,
              offset: const Offset(0, 15),
            ),
          ],
        ),
        child: ClipRRect(
          borderRadius: BorderRadius.circular(borderRadius),
          child: albumArt != null && albumArt!.isNotEmpty
              ? Image.memory(
                  albumArt!,
                  fit: BoxFit.cover,
                  width: size,
                  height: size,
                )
              : Container(
                  color: AppTheme.lightGrey,
                  child: Icon(
                    Icons.music_note_rounded,
                    color: AppTheme.textGrey,
                    size: size * 0.4,
                  ),
                ),
        ),
      ),
    );
  }
}
