import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/models.dart';
import '../providers/providers.dart';
import '../services/audio_player_service.dart';
import '../theme/app_theme.dart';
import '../widgets/widgets.dart';
import 'album_detail_screen.dart';

class ArtistDetailScreen extends StatelessWidget {
  final Artist artist;

  const ArtistDetailScreen({
    super.key,
    required this.artist,
  });

  @override
  Widget build(BuildContext context) {
    final library = context.read<LibraryProvider>();
    final songs = library.getSongsByArtist(artist);
    final albums = library.getAlbumsByArtist(artist);
    final player = context.watch<PlayerProvider>();

    return Scaffold(
      body: CustomScrollView(
        slivers: [
          // Header with artist image
          SliverAppBar(
            expandedHeight: 250,
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
              title: Text(
                artist.displayName,
                style: AppTheme.titleLarge,
              ),
              background: Container(
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.topCenter,
                    end: Alignment.bottomCenter,
                    colors: [
                      const Color(0xFF535353),
                      AppTheme.darkGrey,
                    ],
                  ),
                ),
                child: artist.artistImage != null && artist.artistImage!.isNotEmpty
                    ? ShaderMask(
                        shaderCallback: (rect) {
                          return LinearGradient(
                            begin: Alignment.topCenter,
                            end: Alignment.bottomCenter,
                            colors: [
                              Colors.black,
                              Colors.transparent,
                            ],
                          ).createShader(
                            Rect.fromLTRB(0, 0, rect.width, rect.height),
                          );
                        },
                        blendMode: BlendMode.dstIn,
                        child: Image.memory(
                          artist.artistImage!,
                          fit: BoxFit.cover,
                          width: double.infinity,
                        ),
                      )
                    : Center(
                        child: Icon(
                          Icons.person_rounded,
                          size: 100,
                          color: AppTheme.textGrey.withValues(alpha:0.5),
                        ),
                      ),
              ),
            ),
          ),

          // Artist stats
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              child: Text(
                '${artist.albumCount} albums • ${artist.songCount} songs',
                style: AppTheme.bodySmall,
              ),
            ),
          ),

          // Play controls
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              child: Row(
                children: [
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
                  const SizedBox(width: 8),
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
                  const Spacer(),
                  // More options
                  IconButton(
                    icon: const Icon(Icons.more_vert),
                    color: AppTheme.textGrey,
                    onPressed: () {
                      // Show artist options
                    },
                  ),
                ],
              ),
            ),
          ),

          // Popular songs section
          if (songs.isNotEmpty) ...[
            const SliverToBoxAdapter(
              child: SectionHeader(title: 'Popular'),
            ),
            SliverList(
              delegate: SliverChildBuilderDelegate(
                (context, index) {
                  final song = songs[index];
                  final isPlaying = player.currentSong?.id == song.id;

                  return SongTile(
                    song: song,
                    index: index,
                    showTrackNumber: true,
                    showAlbumArt: true,
                    isPlaying: isPlaying,
                    onTap: () {
                      player.playQueue(songs, startIndex: index);
                    },
                    onMoreTap: () => SongOptionsSheet.show(context, song),
                  );
                },
                childCount: songs.length.clamp(0, 5),
              ),
            ),
            if (songs.length > 5)
              SliverToBoxAdapter(
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  child: OutlinedButton(
                    onPressed: () {
                      // Show all songs
                    },
                    child: const Text('See all songs'),
                  ),
                ),
              ),
          ],

          // Albums section
          if (albums.isNotEmpty) ...[
            const SliverToBoxAdapter(
              child: SectionHeader(title: 'Albums'),
            ),
            SliverToBoxAdapter(
              child: SizedBox(
                height: 200,
                child: ListView.builder(
                  scrollDirection: Axis.horizontal,
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  itemCount: albums.length,
                  itemBuilder: (context, index) {
                    final album = albums[index];
                    return Padding(
                      padding: const EdgeInsets.only(right: 16),
                      child: AlbumCard(
                        album: album,
                        onTap: () => Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) => AlbumDetailScreen(album: album),
                          ),
                        ),
                      ),
                    );
                  },
                ),
              ),
            ),
          ],

          // Spacing for mini player
          const SliverToBoxAdapter(
            child: SizedBox(height: 100),
          ),
        ],
      ),
    );
  }
}
