import 'package:flutter/material.dart';
import '../models/models.dart';
import '../theme/app_theme.dart';
import 'album_art.dart';

class AlbumCard extends StatelessWidget {
  final Album album;
  final VoidCallback? onTap;
  final double width;

  const AlbumCard({
    super.key,
    required this.album,
    this.onTap,
    this.width = 150,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: width,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            AlbumArt(
              albumArt: album.albumArt,
              size: width,
              borderRadius: 8,
              showShadow: true,
            ),
            const SizedBox(height: 12),
            Text(
              album.displayName,
              style: AppTheme.titleSmall,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
            const SizedBox(height: 4),
            Text(
              album.displayArtist,
              style: AppTheme.bodySmall,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ],
        ),
      ),
    );
  }
}

class AlbumCardCompact extends StatelessWidget {
  final Album album;
  final VoidCallback? onTap;

  const AlbumCardCompact({
    super.key,
    required this.album,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(8),
        child: Container(
          decoration: BoxDecoration(
            color: AppTheme.cardGrey,
            borderRadius: BorderRadius.circular(8),
          ),
          child: Row(
            children: [
              AlbumArt(
                albumArt: album.albumArt,
                size: 56,
                borderRadius: 8,
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  album.displayName,
                  style: AppTheme.titleSmall,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              const SizedBox(width: 8),
            ],
          ),
        ),
      ),
    );
  }
}

class AlbumListTile extends StatelessWidget {
  final Album album;
  final VoidCallback? onTap;
  final VoidCallback? onMoreTap;

  const AlbumListTile({
    super.key,
    required this.album,
    this.onTap,
    this.onMoreTap,
  });

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          child: Row(
            children: [
              AlbumArt(
                albumArt: album.albumArt,
                size: 56,
                borderRadius: 4,
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      album.displayName,
                      style: AppTheme.titleSmall,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    const SizedBox(height: 4),
                    Text(
                      '${album.displayArtist} • ${album.songCount} songs',
                      style: AppTheme.bodySmall,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],
                ),
              ),
              if (onMoreTap != null)
                IconButton(
                  icon: const Icon(Icons.more_vert, size: 20),
                  color: AppTheme.textGrey,
                  onPressed: onMoreTap,
                ),
            ],
          ),
        ),
      ),
    );
  }
}
