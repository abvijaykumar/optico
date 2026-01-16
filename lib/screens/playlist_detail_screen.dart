import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/models.dart';
import '../providers/providers.dart';
import '../theme/app_theme.dart';
import '../widgets/widgets.dart';

class PlaylistDetailScreen extends StatelessWidget {
  final Playlist playlist;

  const PlaylistDetailScreen({
    super.key,
    required this.playlist,
  });

  @override
  Widget build(BuildContext context) {
    final player = context.watch<PlayerProvider>();
    final songs = playlist.songs;

    return Scaffold(
      body: CustomScrollView(
        slivers: [
          // Collapsing app bar with playlist cover
          SliverAppBar(
            expandedHeight: 300,
            pinned: true,
            backgroundColor: AppTheme.darkGrey,
            leading: IconButton(
              icon: Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: Colors.black.withOpacity(0.5),
                  shape: BoxShape.circle,
                ),
                child: const Icon(Icons.arrow_back, size: 20),
              ),
              onPressed: () => Navigator.pop(context),
            ),
            flexibleSpace: FlexibleSpaceBar(
              background: Container(
                decoration: BoxDecoration(
                  gradient: AppTheme.dynamicGradient(
                    _getPlaylistColor(),
                  ),
                ),
                child: SafeArea(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const SizedBox(height: 40),
                      _buildPlaylistCover(),
                    ],
                  ),
                ),
              ),
            ),
          ),

          // Playlist info
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    playlist.name,
                    style: AppTheme.headlineMedium,
                  ),
                  if (playlist.description != null &&
                      playlist.description!.isNotEmpty) ...[
                    const SizedBox(height: 8),
                    Text(
                      playlist.description!,
                      style: AppTheme.bodyMedium.copyWith(
                        color: AppTheme.textGrey,
                      ),
                    ),
                  ],
                  const SizedBox(height: 8),
                  Text(
                    '${songs.length} songs • ${playlist.totalDurationString}',
                    style: AppTheme.bodySmall,
                  ),
                ],
              ),
            ),
          ),

          // Play controls
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: Row(
                children: [
                  if (!playlist.isSystemPlaylist) ...[
                    IconButton(
                      icon: const Icon(Icons.download_outlined),
                      color: AppTheme.textGrey,
                      onPressed: () {
                        // Download playlist
                      },
                    ),
                    IconButton(
                      icon: const Icon(Icons.more_vert),
                      color: AppTheme.textGrey,
                      onPressed: () {
                        // Show playlist options
                      },
                    ),
                  ],
                  const Spacer(),
                  // Shuffle button
                  IconButton(
                    icon: const Icon(Icons.shuffle),
                    color: player.shuffleMode == ShuffleMode.on
                        ? AppTheme.primaryGreen
                        : AppTheme.textGrey,
                    onPressed: () {
                      player.toggleShuffleMode();
                    },
                  ),
                  // Play button
                  FloatingActionButton(
                    onPressed: songs.isNotEmpty
                        ? () {
                            player.playQueue(songs, startIndex: 0);
                          }
                        : null,
                    backgroundColor: songs.isNotEmpty
                        ? AppTheme.primaryGreen
                        : AppTheme.lightGrey,
                    child: Icon(
                      Icons.play_arrow_rounded,
                      size: 32,
                      color: songs.isNotEmpty ? AppTheme.black : AppTheme.textGrey,
                    ),
                  ),
                ],
              ),
            ),
          ),

          const SliverToBoxAdapter(
            child: SizedBox(height: 16),
          ),

          // Songs list
          if (songs.isEmpty)
            SliverFillRemaining(
              child: Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(
                      Icons.music_note_outlined,
                      size: 64,
                      color: AppTheme.textGrey,
                    ),
                    const SizedBox(height: 16),
                    Text(
                      'This playlist is empty',
                      style: AppTheme.bodyMedium.copyWith(
                        color: AppTheme.textGrey,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      'Add songs to get started',
                      style: AppTheme.bodySmall,
                    ),
                  ],
                ),
              ),
            )
          else
            SliverList(
              delegate: SliverChildBuilderDelegate(
                (context, index) {
                  final song = songs[index];
                  final isPlaying = player.currentSong?.id == song.id;

                  return SongTile(
                    song: song,
                    showAlbumArt: true,
                    isPlaying: isPlaying,
                    onTap: () {
                      player.playQueue(songs, startIndex: index);
                    },
                    onMoreTap: () => _showSongOptions(context, song),
                  );
                },
                childCount: songs.length,
              ),
            ),

          // Spacing for mini player
          const SliverToBoxAdapter(
            child: SizedBox(height: 100),
          ),
        ],
      ),
    );
  }

  Widget _buildPlaylistCover() {
    if (playlist.songs.isEmpty) {
      return Container(
        width: 180,
        height: 180,
        decoration: BoxDecoration(
          color: AppTheme.lightGrey,
          borderRadius: BorderRadius.circular(8),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.4),
              blurRadius: 30,
              offset: const Offset(0, 15),
            ),
          ],
        ),
        child: Icon(
          playlist.isSystemPlaylist && playlist.name == 'Liked Songs'
              ? Icons.favorite
              : Icons.queue_music_rounded,
          color: AppTheme.textGrey,
          size: 80,
        ),
      );
    }

    if (playlist.songs.length >= 4) {
      return Container(
        width: 180,
        height: 180,
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(8),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.4),
              blurRadius: 30,
              offset: const Offset(0, 15),
            ),
          ],
        ),
        child: ClipRRect(
          borderRadius: BorderRadius.circular(8),
          child: Column(
            children: [
              Row(
                children: [
                  _buildGridItem(playlist.songs[0], 90),
                  _buildGridItem(playlist.songs[1], 90),
                ],
              ),
              Row(
                children: [
                  _buildGridItem(playlist.songs[2], 90),
                  _buildGridItem(playlist.songs[3], 90),
                ],
              ),
            ],
          ),
        ),
      );
    }

    return AlbumArtHero(
      albumArt: playlist.songs.first.albumArt,
      heroTag: 'playlist-${playlist.id}',
      size: 180,
      borderRadius: 8,
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

  Color _getPlaylistColor() {
    if (playlist.isSystemPlaylist && playlist.name == 'Liked Songs') {
      return const Color(0xFF450AF5);
    }
    return const Color(0xFF535353);
  }

  void _showSongOptions(BuildContext context, Song song) {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      builder: (ctx) => Container(
        decoration: const BoxDecoration(
          color: AppTheme.mediumGrey,
          borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
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
            Padding(
              padding: const EdgeInsets.all(20),
              child: Row(
                children: [
                  AlbumArt(
                    albumArt: song.albumArt,
                    size: 56,
                    borderRadius: 4,
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          song.displayTitle,
                          style: AppTheme.titleMedium,
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
                ],
              ),
            ),
            const Divider(height: 1, color: AppTheme.lightGrey),
            if (!playlist.isSystemPlaylist)
              _buildOption(
                context,
                icon: Icons.remove_circle_outline,
                title: 'Remove from playlist',
                onTap: () async {
                  Navigator.pop(context);
                  await context
                      .read<LibraryProvider>()
                      .removeSongFromPlaylist(playlist.id, song.id);
                },
              ),
            _buildOption(
              context,
              icon: Icons.queue_music,
              title: 'Add to queue',
              onTap: () {
                context.read<PlayerProvider>().addToQueue(song);
                Navigator.pop(context);
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Added to queue')),
                );
              },
            ),
            _buildOption(
              context,
              icon: Icons.skip_next,
              title: 'Play next',
              onTap: () {
                context.read<PlayerProvider>().addToQueueNext(song);
                Navigator.pop(context);
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Will play next')),
                );
              },
            ),
            const SizedBox(height: 16),
          ],
        ),
      ),
    );
  }

  Widget _buildOption(
    BuildContext context, {
    required IconData icon,
    required String title,
    required VoidCallback onTap,
  }) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
          child: Row(
            children: [
              Icon(icon, color: AppTheme.white, size: 24),
              const SizedBox(width: 16),
              Text(title, style: AppTheme.bodyLarge),
            ],
          ),
        ),
      ),
    );
  }
}
