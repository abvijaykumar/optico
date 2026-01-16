import 'package:flutter/material.dart';
import '../models/models.dart';
import '../theme/app_theme.dart';
import 'album_art.dart';

class PlaylistCard extends StatelessWidget {
  final Playlist playlist;
  final VoidCallback? onTap;
  final double width;

  const PlaylistCard({
    super.key,
    required this.playlist,
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
            _buildCover(),
            const SizedBox(height: 12),
            Text(
              playlist.name,
              style: AppTheme.titleSmall,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
            const SizedBox(height: 4),
            Text(
              '${playlist.songCount} songs',
              style: AppTheme.bodySmall,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildCover() {
    if (playlist.songs.isEmpty) {
      return _buildEmptyPlaylistCover();
    }

    // Create a 2x2 grid of album arts if we have enough songs
    if (playlist.songs.length >= 4) {
      return _buildGridCover();
    }

    // Use first song's album art
    return AlbumArt(
      albumArt: playlist.songs.first.albumArt,
      size: width,
      borderRadius: 8,
      showShadow: true,
      placeholderIcon: Icons.queue_music_rounded,
    );
  }

  Widget _buildEmptyPlaylistCover() {
    return Container(
      width: width,
      height: width,
      decoration: BoxDecoration(
        color: AppTheme.lightGrey,
        borderRadius: BorderRadius.circular(8),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.3),
            blurRadius: 20,
            offset: const Offset(0, 10),
          ),
        ],
      ),
      child: Icon(
        Icons.queue_music_rounded,
        color: AppTheme.textGrey,
        size: width * 0.4,
      ),
    );
  }

  Widget _buildGridCover() {
    final halfWidth = width / 2;
    return Container(
      width: width,
      height: width,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(8),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.3),
            blurRadius: 20,
            offset: const Offset(0, 10),
          ),
        ],
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(8),
        child: Column(
          children: [
            Row(
              children: [
                _buildGridItem(playlist.songs[0], halfWidth),
                _buildGridItem(playlist.songs[1], halfWidth),
              ],
            ),
            Row(
              children: [
                _buildGridItem(playlist.songs[2], halfWidth),
                _buildGridItem(playlist.songs[3], halfWidth),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildGridItem(Song song, double size) {
    if (song.albumArt != null && song.albumArt!.isNotEmpty) {
      return Image.memory(
        song.albumArt!,
        width: size,
        height: size,
        fit: BoxFit.cover,
      );
    }
    return Container(
      width: size,
      height: size,
      color: AppTheme.lightGrey,
      child: Icon(
        Icons.music_note_rounded,
        color: AppTheme.textGrey,
        size: size * 0.4,
      ),
    );
  }
}

class PlaylistListTile extends StatelessWidget {
  final Playlist playlist;
  final VoidCallback? onTap;
  final VoidCallback? onMoreTap;

  const PlaylistListTile({
    super.key,
    required this.playlist,
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
              _buildCover(),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      playlist.name,
                      style: AppTheme.titleSmall,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    const SizedBox(height: 4),
                    Text(
                      '${playlist.songCount} songs • ${playlist.totalDurationString}',
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

  Widget _buildCover() {
    if (playlist.songs.isEmpty) {
      return Container(
        width: 56,
        height: 56,
        decoration: BoxDecoration(
          color: AppTheme.lightGrey,
          borderRadius: BorderRadius.circular(4),
        ),
        child: const Icon(
          Icons.queue_music_rounded,
          color: AppTheme.textGrey,
          size: 28,
        ),
      );
    }

    return AlbumArt(
      albumArt: playlist.songs.first.albumArt,
      size: 56,
      borderRadius: 4,
      placeholderIcon: Icons.queue_music_rounded,
    );
  }
}
