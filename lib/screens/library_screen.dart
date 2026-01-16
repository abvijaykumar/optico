import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/models.dart';
import '../providers/providers.dart';
import '../theme/app_theme.dart';
import '../widgets/widgets.dart';
import 'album_detail_screen.dart';
import 'artist_detail_screen.dart';
import 'playlist_detail_screen.dart';

enum LibraryFilter { playlists, artists, albums, songs }

class LibraryScreen extends StatefulWidget {
  const LibraryScreen({super.key});

  @override
  State<LibraryScreen> createState() => _LibraryScreenState();
}

class _LibraryScreenState extends State<LibraryScreen> {
  LibraryFilter _currentFilter = LibraryFilter.playlists;
  bool _isGridView = false;

  @override
  Widget build(BuildContext context) {
    return Consumer<LibraryProvider>(
      builder: (context, library, child) {
        return CustomScrollView(
          slivers: [
            // App bar
            SliverAppBar(
              floating: true,
              pinned: true,
              backgroundColor: AppTheme.darkGrey,
              title: const Text(
                'Your Library',
                style: AppTheme.headlineMedium,
              ),
              actions: [
                IconButton(
                  icon: const Icon(Icons.search),
                  onPressed: () {
                    // Navigate to search
                  },
                ),
                IconButton(
                  icon: const Icon(Icons.add),
                  onPressed: () => _showCreatePlaylistDialog(context),
                ),
              ],
              bottom: PreferredSize(
                preferredSize: const Size.fromHeight(60),
                child: _buildFilterChips(),
              ),
            ),

            // Sort and view options
            SliverToBoxAdapter(
              child: _buildSortBar(),
            ),

            // Content based on filter
            _buildContent(library),

            // Spacing for mini player
            const SliverToBoxAdapter(
              child: SizedBox(height: 80),
            ),
          ],
        );
      },
    );
  }

  Widget _buildFilterChips() {
    return Container(
      height: 60,
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: ListView(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 16),
        children: [
          _buildFilterChip(LibraryFilter.playlists, 'Playlists'),
          _buildFilterChip(LibraryFilter.artists, 'Artists'),
          _buildFilterChip(LibraryFilter.albums, 'Albums'),
          _buildFilterChip(LibraryFilter.songs, 'Songs'),
        ],
      ),
    );
  }

  Widget _buildFilterChip(LibraryFilter filter, String label) {
    final isSelected = _currentFilter == filter;
    return Padding(
      padding: const EdgeInsets.only(right: 8),
      child: FilterChip(
        label: Text(label),
        selected: isSelected,
        onSelected: (selected) {
          setState(() => _currentFilter = filter);
        },
        backgroundColor: AppTheme.lightGrey,
        selectedColor: AppTheme.primaryGreen,
        labelStyle: TextStyle(
          color: isSelected ? AppTheme.black : AppTheme.white,
          fontWeight: FontWeight.w500,
        ),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(20),
        ),
        side: BorderSide.none,
        showCheckmark: false,
        padding: const EdgeInsets.symmetric(horizontal: 8),
      ),
    );
  }

  Widget _buildSortBar() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Row(
        children: [
          Icon(
            Icons.swap_vert,
            color: AppTheme.white,
            size: 20,
          ),
          const SizedBox(width: 8),
          Text(
            'Recently added',
            style: AppTheme.bodyMedium,
          ),
          const Spacer(),
          IconButton(
            icon: Icon(
              _isGridView ? Icons.view_list : Icons.grid_view,
              size: 20,
            ),
            onPressed: () {
              setState(() => _isGridView = !_isGridView);
            },
            color: AppTheme.white,
          ),
        ],
      ),
    );
  }

  Widget _buildContent(LibraryProvider library) {
    switch (_currentFilter) {
      case LibraryFilter.playlists:
        return _buildPlaylistsList(library);
      case LibraryFilter.artists:
        return _buildArtistsList(library);
      case LibraryFilter.albums:
        return _buildAlbumsList(library);
      case LibraryFilter.songs:
        return _buildSongsList(library);
    }
  }

  Widget _buildPlaylistsList(LibraryProvider library) {
    final playlists = library.playlists;

    // Add "Liked Songs" as first item
    final allItems = <Widget>[
      _buildLikedSongsItem(library),
      ...playlists.map((p) => PlaylistListTile(
            playlist: p,
            onTap: () => _navigateToPlaylist(context, p),
            onMoreTap: () => _showPlaylistOptions(context, p),
          )),
    ];

    return SliverList(
      delegate: SliverChildBuilderDelegate(
        (context, index) => allItems[index],
        childCount: allItems.length,
      ),
    );
  }

  Widget _buildLikedSongsItem(LibraryProvider library) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: () {
          // Navigate to liked songs
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (context) => PlaylistDetailScreen(
                playlist: Playlist(
                  id: 'liked',
                  name: 'Liked Songs',
                  songs: library.favoriteSongs,
                  createdAt: DateTime.now(),
                  updatedAt: DateTime.now(),
                  isSystemPlaylist: true,
                ),
              ),
            ),
          );
        },
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          child: Row(
            children: [
              Container(
                width: 56,
                height: 56,
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                    colors: [
                      Color(0xFF450AF5),
                      Color(0xFFC4EFD9),
                    ],
                  ),
                  borderRadius: BorderRadius.circular(4),
                ),
                child: const Icon(
                  Icons.favorite,
                  color: Colors.white,
                  size: 24,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Liked Songs',
                      style: AppTheme.titleSmall,
                    ),
                    const SizedBox(height: 4),
                    Text(
                      'Playlist • ${library.favoriteSongs.length} songs',
                      style: AppTheme.bodySmall,
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildArtistsList(LibraryProvider library) {
    if (_isGridView) {
      return SliverPadding(
        padding: const EdgeInsets.all(16),
        sliver: SliverGrid(
          gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
            crossAxisCount: 3,
            mainAxisSpacing: 16,
            crossAxisSpacing: 16,
            childAspectRatio: 0.8,
          ),
          delegate: SliverChildBuilderDelegate(
            (context, index) {
              final artist = library.artists[index];
              return ArtistCard(
                artist: artist,
                size: 100,
                onTap: () => _navigateToArtist(context, artist),
              );
            },
            childCount: library.artists.length,
          ),
        ),
      );
    }

    return SliverList(
      delegate: SliverChildBuilderDelegate(
        (context, index) {
          final artist = library.artists[index];
          return ArtistListTile(
            artist: artist,
            onTap: () => _navigateToArtist(context, artist),
          );
        },
        childCount: library.artists.length,
      ),
    );
  }

  Widget _buildAlbumsList(LibraryProvider library) {
    if (_isGridView) {
      return SliverPadding(
        padding: const EdgeInsets.all(16),
        sliver: SliverGrid(
          gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
            crossAxisCount: 2,
            mainAxisSpacing: 16,
            crossAxisSpacing: 16,
            childAspectRatio: 0.8,
          ),
          delegate: SliverChildBuilderDelegate(
            (context, index) {
              final album = library.albums[index];
              return AlbumCard(
                album: album,
                width: double.infinity,
                onTap: () => _navigateToAlbum(context, album),
              );
            },
            childCount: library.albums.length,
          ),
        ),
      );
    }

    return SliverList(
      delegate: SliverChildBuilderDelegate(
        (context, index) {
          final album = library.albums[index];
          return AlbumListTile(
            album: album,
            onTap: () => _navigateToAlbum(context, album),
          );
        },
        childCount: library.albums.length,
      ),
    );
  }

  Widget _buildSongsList(LibraryProvider library) {
    final player = context.read<PlayerProvider>();

    return SliverList(
      delegate: SliverChildBuilderDelegate(
        (context, index) {
          final song = library.songs[index];
          return SongTile(
            song: song,
            isPlaying: player.currentSong?.id == song.id,
            onTap: () {
              player.playQueue(library.songs, startIndex: index);
            },
            onMoreTap: () => SongOptionsSheet.show(context, song),
          );
        },
        childCount: library.songs.length,
      ),
    );
  }

  void _navigateToPlaylist(BuildContext context, Playlist playlist) {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => PlaylistDetailScreen(playlist: playlist),
      ),
    );
  }

  void _navigateToArtist(BuildContext context, Artist artist) {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => ArtistDetailScreen(artist: artist),
      ),
    );
  }

  void _navigateToAlbum(BuildContext context, Album album) {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => AlbumDetailScreen(album: album),
      ),
    );
  }

  void _showCreatePlaylistDialog(BuildContext context) async {
    final controller = TextEditingController();
    final name = await showDialog<String>(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: AppTheme.mediumGrey,
        title: const Text('Create playlist', style: AppTheme.titleLarge),
        content: TextField(
          controller: controller,
          autofocus: true,
          style: AppTheme.bodyLarge,
          decoration: const InputDecoration(hintText: 'Playlist name'),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(context, controller.text),
            child: const Text('Create'),
          ),
        ],
      ),
    );

    if (name != null && name.isNotEmpty) {
      await context.read<LibraryProvider>().createPlaylist(name);
    }
  }

  void _showPlaylistOptions(BuildContext context, Playlist playlist) {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      builder: (context) => Container(
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
              child: Text(playlist.name, style: AppTheme.titleLarge),
            ),
            _buildOptionItem(
              icon: Icons.edit,
              title: 'Edit playlist',
              onTap: () {
                Navigator.pop(context);
                // Edit playlist
              },
            ),
            _buildOptionItem(
              icon: Icons.delete_outline,
              title: 'Delete playlist',
              onTap: () async {
                Navigator.pop(context);
                await context.read<LibraryProvider>().deletePlaylist(playlist.id);
              },
            ),
            const SizedBox(height: 16),
          ],
        ),
      ),
    );
  }

  Widget _buildOptionItem({
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
