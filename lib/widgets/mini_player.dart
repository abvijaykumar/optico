import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/models.dart';
import '../providers/providers.dart';
import '../theme/app_theme.dart';
import 'album_art.dart';

class MiniPlayer extends StatelessWidget {
  final VoidCallback? onTap;

  const MiniPlayer({
    super.key,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Consumer<PlayerProvider>(
      builder: (context, player, child) {
        final song = player.currentSong;
        if (song == null) return const SizedBox.shrink();

        return GestureDetector(
          onTap: onTap,
          child: Container(
            height: 64,
            margin: const EdgeInsets.symmetric(horizontal: 8),
            decoration: BoxDecoration(
              color: AppTheme.cardGrey,
              borderRadius: BorderRadius.circular(8),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.3),
                  blurRadius: 10,
                  offset: const Offset(0, -2),
                ),
              ],
            ),
            child: Column(
              children: [
                // Progress bar
                _buildProgressBar(player),
                // Content
                Expanded(
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 8),
                    child: Row(
                      children: [
                        // Album art
                        AlbumArt(
                          albumArt: song.albumArt,
                          size: 48,
                          borderRadius: 4,
                        ),
                        const SizedBox(width: 12),
                        // Song info
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Text(
                                song.displayTitle,
                                style: AppTheme.titleSmall,
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
                        // Favorite button
                        _buildFavoriteButton(context, song),
                        // Play/Pause button
                        _buildPlayPauseButton(player),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildProgressBar(PlayerProvider player) {
    return SizedBox(
      height: 2,
      child: LinearProgressIndicator(
        value: player.progress,
        backgroundColor: Colors.transparent,
        valueColor: const AlwaysStoppedAnimation<Color>(AppTheme.primaryGreen),
      ),
    );
  }

  Widget _buildFavoriteButton(BuildContext context, Song song) {
    return IconButton(
      icon: Icon(
        song.isFavorite ? Icons.favorite : Icons.favorite_border,
        size: 22,
      ),
      color: song.isFavorite ? AppTheme.primaryGreen : AppTheme.textGrey,
      onPressed: () {
        context.read<LibraryProvider>().toggleFavorite(song);
      },
      splashRadius: 20,
    );
  }

  Widget _buildPlayPauseButton(PlayerProvider player) {
    return IconButton(
      icon: Icon(
        player.isPlaying
            ? Icons.pause_rounded
            : Icons.play_arrow_rounded,
        size: 32,
      ),
      color: AppTheme.white,
      onPressed: () => player.togglePlayPause(),
      splashRadius: 24,
    );
  }
}

class MiniPlayerSliding extends StatelessWidget {
  final VoidCallback? onTap;
  final double slideProgress;

  const MiniPlayerSliding({
    super.key,
    this.onTap,
    this.slideProgress = 0,
  });

  @override
  Widget build(BuildContext context) {
    return Consumer<PlayerProvider>(
      builder: (context, player, child) {
        final song = player.currentSong;
        if (song == null || !player.isMiniPlayerVisible) {
          return const SizedBox.shrink();
        }

        return Opacity(
          opacity: 1 - slideProgress,
          child: MiniPlayer(onTap: onTap),
        );
      },
    );
  }
}
