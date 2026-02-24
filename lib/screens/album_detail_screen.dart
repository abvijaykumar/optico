import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/models.dart';
import '../providers/providers.dart';
import '../services/audio_player_service.dart';
import '../theme/app_theme.dart';
import '../widgets/widgets.dart';

class AlbumDetailScreen extends StatelessWidget {
  final Album album;

  const AlbumDetailScreen({
    super.key,
    required this.album,
  });

  @override
  Widget build(BuildContext context) {
    final library = context.read<LibraryProvider>();
    final songs = library.getSongsByAlbum(album);
    final player = context.watch<PlayerProvider>();

    return Scaffold(
      body: CustomScrollView(
        slivers: [
          // Collapsing app bar with album art
          SliverAppBar(
            expandedHeight: 300,
            pinned: true,
            backgroundColor: AppTheme.darkGrey,
            leading: IconButton(
              icon: Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: Colors.black.withValues(alpha:0.5),
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
                    _getDominantColor(),
                  ),
                ),
                child: SafeArea(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const SizedBox(height: 40),
                      AlbumArtHero(
                        albumArt: album.albumArt,
                        heroTag: 'album-${album.id}',
                        size: 180,
                        borderRadius: 8,
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),

          // Album info
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    album.displayName,
                    style: AppTheme.headlineMedium,
                  ),
                  const SizedBox(height: 8),
                  GestureDetector(
                    onTap: () {
                      // Navigate to artist
                    },
                    child: Text(
                      album.displayArtist,
                      style: AppTheme.bodyMedium.copyWith(
                        color: AppTheme.textGrey,
                      ),
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    '${album.year ?? ''} • ${songs.length} songs • ${album.totalDurationString}',
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
                  // Favorite button
                  IconButton(
                    icon: const Icon(Icons.favorite_border),
                    color: AppTheme.textGrey,
                    onPressed: () {
                      // Toggle album favorite
                    },
                  ),
                  IconButton(
                    icon: const Icon(Icons.download_outlined),
                    color: AppTheme.textGrey,
                    onPressed: () {
                      // Download album
                    },
                  ),
                  IconButton(
                    icon: const Icon(Icons.more_vert),
                    color: AppTheme.textGrey,
                    onPressed: () {
                      // Show album options
                    },
                  ),
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
                    onPressed: () {
                      player.playQueue(songs, startIndex: 0);
                    },
                    backgroundColor: AppTheme.primaryGreen,
                    child: const Icon(
                      Icons.play_arrow_rounded,
                      size: 32,
                      color: AppTheme.black,
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
          SliverList(
            delegate: SliverChildBuilderDelegate(
              (context, index) {
                final song = songs[index];
                final isPlaying = player.currentSong?.id == song.id;

                return SongTile(
                  song: song,
                  index: index,
                  showTrackNumber: true,
                  showAlbumArt: false,
                  isPlaying: isPlaying,
                  onTap: () {
                    player.playQueue(songs, startIndex: index);
                  },
                  onMoreTap: () => SongOptionsSheet.show(context, song),
                );
              },
              childCount: songs.length,
            ),
          ),

          // Album info at bottom
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Divider(color: AppTheme.lightGrey),
                  const SizedBox(height: 16),
                  Text(
                    album.year?.toString() ?? '',
                    style: AppTheme.bodySmall,
                  ),
                  const SizedBox(height: 4),
                  Text(
                    '${songs.length} songs • ${album.totalDurationString}',
                    style: AppTheme.bodySmall,
                  ),
                ],
              ),
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

  Color _getDominantColor() {
    // In a real app, you would extract the dominant color from the album art
    // For now, return a default color
    return const Color(0xFF535353);
  }
}
