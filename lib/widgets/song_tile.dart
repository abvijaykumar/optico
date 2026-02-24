import 'package:flutter/material.dart';
import '../models/models.dart';
import '../theme/app_theme.dart';
import 'album_art.dart';

class SongTile extends StatelessWidget {
  final Song song;
  final VoidCallback? onTap;
  final VoidCallback? onMoreTap;
  final bool isPlaying;
  final bool showAlbumArt;
  final bool showTrackNumber;
  final int? index;

  const SongTile({
    super.key,
    required this.song,
    this.onTap,
    this.onMoreTap,
    this.isPlaying = false,
    this.showAlbumArt = true,
    this.showTrackNumber = false,
    this.index,
  });

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        splashColor: AppTheme.lightGrey.withValues(alpha:0.3),
        highlightColor: AppTheme.lightGrey.withValues(alpha:0.2),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          child: Row(
            children: [
              if (showTrackNumber && index != null) ...[
                SizedBox(
                  width: 32,
                  child: Text(
                    isPlaying ? '' : '${index! + 1}',
                    style: AppTheme.bodyMedium.copyWith(
                      color: isPlaying ? AppTheme.primaryGreen : AppTheme.textGrey,
                    ),
                    textAlign: TextAlign.center,
                  ),
                ),
                if (isPlaying)
                  const Icon(
                    Icons.volume_up_rounded,
                    color: AppTheme.primaryGreen,
                    size: 20,
                  ),
                const SizedBox(width: 16),
              ] else if (showAlbumArt) ...[
                AlbumArt(
                  albumArt: song.albumArt,
                  size: 48,
                  borderRadius: 4,
                ),
                const SizedBox(width: 12),
              ],
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(
                      song.displayTitle,
                      style: AppTheme.titleSmall.copyWith(
                        color: isPlaying ? AppTheme.primaryGreen : AppTheme.white,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    const SizedBox(height: 4),
                    Text(
                      song.displayArtist,
                      style: AppTheme.bodySmall,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],
                ),
              ),
              if (song.isFavorite)
                Padding(
                  padding: const EdgeInsets.only(right: 8),
                  child: Icon(
                    Icons.favorite,
                    color: AppTheme.primaryGreen,
                    size: 18,
                  ),
                ),
              if (onMoreTap != null)
                IconButton(
                  icon: const Icon(Icons.more_vert, size: 20),
                  color: AppTheme.textGrey,
                  onPressed: onMoreTap,
                  splashRadius: 20,
                ),
            ],
          ),
        ),
      ),
    );
  }
}

class SongTileCompact extends StatelessWidget {
  final Song song;
  final VoidCallback? onTap;
  final bool isPlaying;

  const SongTileCompact({
    super.key,
    required this.song,
    this.onTap,
    this.isPlaying = false,
  });

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
          child: Row(
            children: [
              AlbumArt(
                albumArt: song.albumArt,
                size: 40,
                borderRadius: 4,
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(
                      song.displayTitle,
                      style: AppTheme.bodyMedium.copyWith(
                        color: isPlaying ? AppTheme.primaryGreen : AppTheme.white,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    Text(
                      song.displayArtist,
                      style: AppTheme.bodySmall,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],
                ),
              ),
              if (isPlaying)
                const Icon(
                  Icons.equalizer,
                  color: AppTheme.primaryGreen,
                  size: 20,
                ),
            ],
          ),
        ),
      ),
    );
  }
}
