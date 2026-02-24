import 'package:flutter/material.dart' hide RepeatMode;
import 'package:provider/provider.dart';
import '../providers/providers.dart';
import '../services/audio_player_service.dart';
import '../theme/app_theme.dart';
import '../widgets/widgets.dart';

class PlayerScreen extends StatefulWidget {
  const PlayerScreen({super.key});

  @override
  State<PlayerScreen> createState() => _PlayerScreenState();
}

class _PlayerScreenState extends State<PlayerScreen>
    with SingleTickerProviderStateMixin {
  late AnimationController _animationController;

  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 300),
    );
  }

  @override
  void dispose() {
    _animationController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<PlayerProvider>(
      builder: (context, player, child) {
        final song = player.currentSong;
        if (song == null) {
          return const Scaffold(
            backgroundColor: AppTheme.darkGrey,
            body: Center(
              child: Text('No song playing', style: AppTheme.bodyMedium),
            ),
          );
        }

        return Scaffold(
          backgroundColor: AppTheme.darkGrey,
          body: Container(
            decoration: BoxDecoration(
              gradient: AppTheme.dynamicGradient(
                const Color(0xFF535353),
              ),
            ),
            child: SafeArea(
              child: Column(
                children: [
                  // Top bar
                  _buildTopBar(context),

                  // Album art
                  Expanded(
                    child: Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 32),
                      child: Center(
                        child: AlbumArtHero(
                          albumArt: song.albumArt,
                          heroTag: 'now-playing',
                          size: MediaQuery.of(context).size.width - 64,
                          borderRadius: 8,
                        ),
                      ),
                    ),
                  ),

                  // Song info and controls
                  Padding(
                    padding: const EdgeInsets.all(24),
                    child: Column(
                      children: [
                        // Song info
                        _buildSongInfo(context, player),
                        const SizedBox(height: 24),

                        // Progress bar
                        _buildProgressBar(player),
                        const SizedBox(height: 24),

                        // Playback controls
                        _buildPlaybackControls(player),
                        const SizedBox(height: 24),

                        // Additional controls
                        _buildAdditionalControls(context, player),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
        );
      },
    );
  }

  Widget _buildTopBar(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          IconButton(
            icon: const Icon(Icons.keyboard_arrow_down, size: 32),
            onPressed: () => Navigator.pop(context),
          ),
          Column(
            children: [
              Text(
                'PLAYING FROM',
                style: AppTheme.labelSmall.copyWith(
                  letterSpacing: 1,
                ),
              ),
              const SizedBox(height: 4),
              const Text(
                'Your Library',
                style: AppTheme.titleSmall,
              ),
            ],
          ),
          IconButton(
            icon: const Icon(Icons.more_vert),
            onPressed: () {
              final player = context.read<PlayerProvider>();
              if (player.currentSong != null) {
                SongOptionsSheet.show(context, player.currentSong!);
              }
            },
          ),
        ],
      ),
    );
  }

  Widget _buildSongInfo(BuildContext context, PlayerProvider player) {
    final song = player.currentSong!;
    final library = context.read<LibraryProvider>();

    return Row(
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                song.displayTitle,
                style: AppTheme.headlineSmall,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
              const SizedBox(height: 4),
              Text(
                song.displayArtist,
                style: AppTheme.bodyMedium.copyWith(
                  color: AppTheme.textGrey,
                ),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
            ],
          ),
        ),
        IconButton(
          icon: Icon(
            song.isFavorite ? Icons.favorite : Icons.favorite_border,
            size: 28,
          ),
          color: song.isFavorite ? AppTheme.primaryGreen : AppTheme.white,
          onPressed: () => library.toggleFavorite(song),
        ),
      ],
    );
  }

  Widget _buildProgressBar(PlayerProvider player) {
    return StreamBuilder<PositionData>(
      stream: player.audioService.positionDataStream,
      builder: (context, snapshot) {
        final positionData = snapshot.data ??
            PositionData(
              player.position,
              Duration.zero,
              player.duration,
            );

        return Column(
          children: [
            SliderTheme(
              data: SliderTheme.of(context).copyWith(
                trackHeight: 4,
                thumbShape: const RoundSliderThumbShape(
                  enabledThumbRadius: 6,
                  pressedElevation: 0,
                ),
                overlayShape: const RoundSliderOverlayShape(overlayRadius: 16),
              ),
              child: Slider(
                value: positionData.position.inMilliseconds.toDouble().clamp(
                      0,
                      positionData.duration.inMilliseconds.toDouble(),
                    ),
                max: positionData.duration.inMilliseconds.toDouble(),
                onChanged: (value) {
                  player.seek(Duration(milliseconds: value.round()));
                },
                activeColor: AppTheme.white,
                inactiveColor: AppTheme.lightGrey,
              ),
            ),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    _formatDuration(positionData.position),
                    style: AppTheme.bodySmall,
                  ),
                  Text(
                    _formatDuration(positionData.duration),
                    style: AppTheme.bodySmall,
                  ),
                ],
              ),
            ),
          ],
        );
      },
    );
  }

  Widget _buildPlaybackControls(PlayerProvider player) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceEvenly,
      children: [
        // Shuffle
        IconButton(
          icon: const Icon(Icons.shuffle),
          iconSize: 28,
          color: player.shuffleMode == ShuffleMode.on
              ? AppTheme.primaryGreen
              : AppTheme.white,
          onPressed: () => player.toggleShuffleMode(),
        ),

        // Previous
        IconButton(
          icon: const Icon(Icons.skip_previous_rounded),
          iconSize: 40,
          color: AppTheme.white,
          onPressed: player.hasPrevious ? () => player.previous() : null,
        ),

        // Play/Pause
        Container(
          width: 72,
          height: 72,
          decoration: const BoxDecoration(
            color: AppTheme.white,
            shape: BoxShape.circle,
          ),
          child: IconButton(
            icon: Icon(
              player.isPlaying
                  ? Icons.pause_rounded
                  : Icons.play_arrow_rounded,
            ),
            iconSize: 40,
            color: AppTheme.black,
            onPressed: () => player.togglePlayPause(),
          ),
        ),

        // Next
        IconButton(
          icon: const Icon(Icons.skip_next_rounded),
          iconSize: 40,
          color: AppTheme.white,
          onPressed: player.hasNext ? () => player.next() : null,
        ),

        // Repeat
        IconButton(
          icon: Icon(
            player.repeatMode == RepeatMode.one
                ? Icons.repeat_one
                : Icons.repeat,
          ),
          iconSize: 28,
          color: player.repeatMode != RepeatMode.off
              ? AppTheme.primaryGreen
              : AppTheme.white,
          onPressed: () => player.toggleRepeatMode(),
        ),
      ],
    );
  }

  Widget _buildAdditionalControls(BuildContext context, PlayerProvider player) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        IconButton(
          icon: const Icon(Icons.devices),
          color: AppTheme.textGrey,
          onPressed: () {
            // Show devices
          },
        ),
        IconButton(
          icon: const Icon(Icons.share),
          color: AppTheme.textGrey,
          onPressed: () {
            // Share song
          },
        ),
        IconButton(
          icon: const Icon(Icons.queue_music),
          color: AppTheme.textGrey,
          onPressed: () => _showQueue(context, player),
        ),
      ],
    );
  }

  void _showQueue(BuildContext context, PlayerProvider player) {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      isScrollControlled: true,
      builder: (context) => DraggableScrollableSheet(
        initialChildSize: 0.7,
        minChildSize: 0.5,
        maxChildSize: 0.95,
        builder: (context, scrollController) => Container(
          decoration: const BoxDecoration(
            color: AppTheme.mediumGrey,
            borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
          ),
          child: Column(
            children: [
              Container(
                width: 40,
                height: 4,
                margin: const EdgeInsets.only(top: 12),
                decoration: BoxDecoration(
                  color: AppTheme.textGrey,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
              const Padding(
                padding: EdgeInsets.all(20),
                child: Text('Queue', style: AppTheme.titleLarge),
              ),
              if (player.currentSong != null) ...[
                const Padding(
                  padding: EdgeInsets.symmetric(horizontal: 16),
                  child: Align(
                    alignment: Alignment.centerLeft,
                    child: Text('Now Playing', style: AppTheme.labelSmall),
                  ),
                ),
                SongTileCompact(
                  song: player.currentSong!,
                  isPlaying: true,
                ),
                const Divider(color: AppTheme.lightGrey, height: 32),
              ],
              if (player.queue.isNotEmpty) ...[
                const Padding(
                  padding: EdgeInsets.symmetric(horizontal: 16),
                  child: Align(
                    alignment: Alignment.centerLeft,
                    child: Text('Next in queue', style: AppTheme.labelSmall),
                  ),
                ),
                Expanded(
                  child: ReorderableListView.builder(
                    scrollController: scrollController,
                    itemCount: player.queue.length,
                    onReorder: (oldIndex, newIndex) {
                      player.reorderQueue(oldIndex, newIndex);
                    },
                    itemBuilder: (context, index) {
                      final song = player.queue[index];
                      final isCurrentSong = index == player.currentIndex;

                      return Dismissible(
                        key: Key('queue-$index-${song.id}'),
                        direction: DismissDirection.endToStart,
                        onDismissed: (_) {
                          player.removeFromQueue(index);
                        },
                        background: Container(
                          color: AppTheme.errorRed,
                          alignment: Alignment.centerRight,
                          padding: const EdgeInsets.only(right: 16),
                          child: const Icon(Icons.delete, color: AppTheme.white),
                        ),
                        child: SongTileCompact(
                          song: song,
                          isPlaying: isCurrentSong,
                          onTap: () {
                            player.skipToIndex(index);
                          },
                        ),
                      );
                    },
                  ),
                ),
              ] else
                const Expanded(
                  child: Center(
                    child: Text(
                      'Queue is empty',
                      style: AppTheme.bodyMedium,
                    ),
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }

  String _formatDuration(Duration duration) {
    final minutes = duration.inMinutes;
    final seconds = duration.inSeconds % 60;
    return '$minutes:${seconds.toString().padLeft(2, '0')}';
  }
}
