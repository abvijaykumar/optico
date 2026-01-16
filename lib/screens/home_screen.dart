import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/providers.dart';
import '../theme/app_theme.dart';
import '../widgets/widgets.dart';
import 'album_detail_screen.dart';
import 'artist_detail_screen.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Consumer<LibraryProvider>(
      builder: (context, library, child) {
        if (library.isLoading) {
          return const Center(
            child: CircularProgressIndicator(
              color: AppTheme.primaryGreen,
            ),
          );
        }

        if (library.songs.isEmpty) {
          return _buildEmptyState(context);
        }

        return CustomScrollView(
          slivers: [
            // App bar
            SliverAppBar(
              floating: true,
              backgroundColor: AppTheme.darkGrey,
              title: const Text(
                'Good evening',
                style: AppTheme.headlineMedium,
              ),
              actions: [
                IconButton(
                  icon: const Icon(Icons.settings_outlined),
                  onPressed: () => Navigator.pushNamed(context, '/settings'),
                ),
              ],
            ),

            // Quick picks grid
            if (library.recentlyPlayed.isNotEmpty ||
                library.mostPlayed.isNotEmpty ||
                library.albums.isNotEmpty)
              _buildQuickPicks(context, library),

            // Recently played section
            if (library.recentlyPlayed.isNotEmpty) ...[
              SliverToBoxAdapter(
                child: SectionHeader(
                  title: 'Recently played',
                  onSeeAllTap: () {
                    // Navigate to full recently played
                  },
                ),
              ),
              SliverToBoxAdapter(
                child: SizedBox(
                  height: 200,
                  child: ListView.builder(
                    scrollDirection: Axis.horizontal,
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                    itemCount: library.recentlyPlayed.length.clamp(0, 10),
                    itemBuilder: (context, index) {
                      final song = library.recentlyPlayed[index];
                      final album = library.albums.firstWhere(
                        (a) =>
                            a.name == song.album && a.artist == song.artist,
                        orElse: () => library.albums.first,
                      );
                      return Padding(
                        padding: const EdgeInsets.only(right: 16),
                        child: AlbumCard(
                          album: album,
                          onTap: () => _navigateToAlbum(context, album),
                        ),
                      );
                    },
                  ),
                ),
              ),
            ],

            // Your top artists
            if (library.artists.isNotEmpty) ...[
              SliverToBoxAdapter(
                child: SectionHeader(
                  title: 'Your top artists',
                  onSeeAllTap: () {
                    // Navigate to all artists
                  },
                ),
              ),
              SliverToBoxAdapter(
                child: SizedBox(
                  height: 200,
                  child: ListView.builder(
                    scrollDirection: Axis.horizontal,
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                    itemCount: library.artists.length.clamp(0, 10),
                    itemBuilder: (context, index) {
                      final artist = library.artists[index];
                      return Padding(
                        padding: const EdgeInsets.only(right: 16),
                        child: ArtistCard(
                          artist: artist,
                          onTap: () => _navigateToArtist(context, artist),
                        ),
                      );
                    },
                  ),
                ),
              ),
            ],

            // All albums
            if (library.albums.isNotEmpty) ...[
              SliverToBoxAdapter(
                child: SectionHeader(
                  title: 'Browse albums',
                  onSeeAllTap: () {
                    // Navigate to all albums
                  },
                ),
              ),
              SliverToBoxAdapter(
                child: SizedBox(
                  height: 200,
                  child: ListView.builder(
                    scrollDirection: Axis.horizontal,
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                    itemCount: library.albums.length.clamp(0, 20),
                    itemBuilder: (context, index) {
                      final album = library.albums[index];
                      return Padding(
                        padding: const EdgeInsets.only(right: 16),
                        child: AlbumCard(
                          album: album,
                          onTap: () => _navigateToAlbum(context, album),
                        ),
                      );
                    },
                  ),
                ),
              ),
            ],

            // Spacing for mini player
            const SliverToBoxAdapter(
              child: SizedBox(height: 80),
            ),
          ],
        );
      },
    );
  }

  Widget _buildEmptyState(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.library_music_outlined,
              size: 80,
              color: AppTheme.textGrey,
            ),
            const SizedBox(height: 24),
            Text(
              'Your library is empty',
              style: AppTheme.headlineSmall,
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 12),
            Text(
              'Add folders containing your music to start listening',
              style: AppTheme.bodyMedium.copyWith(color: AppTheme.textGrey),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 32),
            ElevatedButton.icon(
              onPressed: () => Navigator.pushNamed(context, '/settings'),
              icon: const Icon(Icons.add),
              label: const Text('Add Music Folders'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildQuickPicks(BuildContext context, LibraryProvider library) {
    // Get items for quick picks grid (mix of recent, favorites, albums)
    final items = <Widget>[];

    // Add some albums
    for (var i = 0; i < library.albums.length.clamp(0, 6); i++) {
      final album = library.albums[i];
      items.add(
        AlbumCardCompact(
          album: album,
          onTap: () => _navigateToAlbum(context, album),
        ),
      );
    }

    if (items.isEmpty) return const SliverToBoxAdapter(child: SizedBox.shrink());

    return SliverPadding(
      padding: const EdgeInsets.all(16),
      sliver: SliverGrid(
        gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
          crossAxisCount: 2,
          mainAxisSpacing: 8,
          crossAxisSpacing: 8,
          mainAxisExtent: 56,
        ),
        delegate: SliverChildBuilderDelegate(
          (context, index) => items[index],
          childCount: items.length,
        ),
      ),
    );
  }

  void _navigateToAlbum(BuildContext context, album) {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => AlbumDetailScreen(album: album),
      ),
    );
  }

  void _navigateToArtist(BuildContext context, artist) {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => ArtistDetailScreen(artist: artist),
      ),
    );
  }
}
