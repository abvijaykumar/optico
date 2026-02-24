import 'dart:async';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/models.dart';
import '../providers/providers.dart';
import '../theme/app_theme.dart';
import '../widgets/widgets.dart';
import 'album_detail_screen.dart';
import 'artist_detail_screen.dart';

class SearchScreen extends StatefulWidget {
  const SearchScreen({super.key});

  @override
  State<SearchScreen> createState() => _SearchScreenState();
}

class _SearchScreenState extends State<SearchScreen> {
  final _searchController = TextEditingController();
  final _focusNode = FocusNode();

  List<Song> _songResults = [];
  List<Album> _albumResults = [];
  List<Artist> _artistResults = [];

  bool _isSearching = false;
  Timer? _debounceTimer;

  @override
  void dispose() {
    _searchController.dispose();
    _focusNode.dispose();
    _debounceTimer?.cancel();
    super.dispose();
  }

  void _onSearchChanged(String query) {
    _debounceTimer?.cancel();

    if (query.isEmpty) {
      setState(() {
        _songResults = [];
        _albumResults = [];
        _artistResults = [];
        _isSearching = false;
      });
      return;
    }

    setState(() => _isSearching = true);

    _debounceTimer = Timer(const Duration(milliseconds: 300), () {
      _performSearch(query);
    });
  }

  Future<void> _performSearch(String query) async {
    final library = context.read<LibraryProvider>();

    final songs = await library.searchSongs(query);
    final albums = library.searchAlbums(query);
    final artists = library.searchArtists(query);

    if (mounted) {
      setState(() {
        _songResults = songs;
        _albumResults = albums;
        _artistResults = artists;
        _isSearching = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final library = context.watch<LibraryProvider>();

    return CustomScrollView(
      slivers: [
        // App bar with search
        SliverAppBar(
          floating: true,
          pinned: true,
          backgroundColor: AppTheme.darkGrey,
          expandedHeight: 120,
          flexibleSpace: FlexibleSpaceBar(
            background: Container(
              alignment: Alignment.bottomCenter,
              padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.end,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Search',
                    style: AppTheme.headlineMedium,
                  ),
                  const SizedBox(height: 16),
                  _buildSearchField(),
                ],
              ),
            ),
          ),
        ),

        // Content
        if (_searchController.text.isEmpty)
          _buildBrowseContent(library)
        else if (_isSearching)
          const SliverFillRemaining(
            child: Center(
              child: CircularProgressIndicator(color: AppTheme.primaryGreen),
            ),
          )
        else
          _buildSearchResults(),

        // Spacing for mini player
        const SliverToBoxAdapter(
          child: SizedBox(height: 80),
        ),
      ],
    );
  }

  Widget _buildSearchField() {
    return TextField(
      controller: _searchController,
      focusNode: _focusNode,
      onChanged: _onSearchChanged,
      style: AppTheme.bodyLarge.copyWith(color: AppTheme.black),
      decoration: InputDecoration(
        hintText: 'What do you want to listen to?',
        hintStyle: AppTheme.bodyMedium.copyWith(color: AppTheme.textGrey),
        prefixIcon: const Icon(Icons.search, color: AppTheme.black),
        suffixIcon: _searchController.text.isNotEmpty
            ? IconButton(
                icon: const Icon(Icons.clear, color: AppTheme.black),
                onPressed: () {
                  _searchController.clear();
                  _onSearchChanged('');
                },
              )
            : null,
        filled: true,
        fillColor: AppTheme.white,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: BorderSide.none,
        ),
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      ),
    );
  }

  Widget _buildBrowseContent(LibraryProvider library) {
    // Show browse categories when not searching
    return SliverToBoxAdapter(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SectionHeader(title: 'Browse your library'),
          _buildBrowseGrid(),
          if (library.recentlyPlayed.isNotEmpty) ...[
            const SectionHeader(title: 'Recent searches'),
            ...library.recentlyPlayed.take(5).map((song) => SongTileCompact(
                  song: song,
                  onTap: () {
                    context.read<PlayerProvider>().playSong(song);
                  },
                )),
          ],
        ],
      ),
    );
  }

  Widget _buildBrowseGrid() {
    return GridView.count(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      crossAxisCount: 2,
      padding: const EdgeInsets.symmetric(horizontal: 16),
      mainAxisSpacing: 16,
      crossAxisSpacing: 16,
      childAspectRatio: 1.8,
      children: [
        _buildBrowseCard('All Songs', Icons.music_note, const Color(0xFF8C67AC)),
        _buildBrowseCard('Albums', Icons.album, const Color(0xFFE8115B)),
        _buildBrowseCard('Artists', Icons.person, const Color(0xFF1E3264)),
        _buildBrowseCard('Playlists', Icons.queue_music, const Color(0xFFE91429)),
        _buildBrowseCard('Favorites', Icons.favorite, const Color(0xFF148A08)),
        _buildBrowseCard('Folders', Icons.folder, const Color(0xFFE13300)),
      ],
    );
  }

  Widget _buildBrowseCard(String title, IconData icon, Color color) {
    return Container(
      decoration: BoxDecoration(
        color: color,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Stack(
        children: [
          Positioned(
            right: -10,
            bottom: -10,
            child: Transform.rotate(
              angle: 0.3,
              child: Icon(
                icon,
                size: 60,
                color: Colors.black.withValues(alpha:0.2),
              ),
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(16),
            child: Text(
              title,
              style: AppTheme.titleMedium,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSearchResults() {
    final hasResults = _songResults.isNotEmpty ||
        _albumResults.isNotEmpty ||
        _artistResults.isNotEmpty;

    if (!hasResults) {
      return SliverFillRemaining(
        child: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                Icons.search_off,
                size: 64,
                color: AppTheme.textGrey,
              ),
              const SizedBox(height: 16),
              Text(
                'No results found for "${_searchController.text}"',
                style: AppTheme.bodyMedium.copyWith(color: AppTheme.textGrey),
                textAlign: TextAlign.center,
              ),
            ],
          ),
        ),
      );
    }

    return SliverList(
      delegate: SliverChildListDelegate([
        // Artists
        if (_artistResults.isNotEmpty) ...[
          const SectionHeaderSmall(title: 'Artists'),
          ..._artistResults.take(3).map((artist) => ArtistListTile(
                artist: artist,
                onTap: () => Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (context) => ArtistDetailScreen(artist: artist),
                  ),
                ),
              )),
        ],

        // Albums
        if (_albumResults.isNotEmpty) ...[
          const SectionHeaderSmall(title: 'Albums'),
          ..._albumResults.take(3).map((album) => AlbumListTile(
                album: album,
                onTap: () => Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (context) => AlbumDetailScreen(album: album),
                  ),
                ),
              )),
        ],

        // Songs
        if (_songResults.isNotEmpty) ...[
          const SectionHeaderSmall(title: 'Songs'),
          ..._songResults.map((song) {
            final player = context.read<PlayerProvider>();
            return SongTile(
              song: song,
              isPlaying: player.currentSong?.id == song.id,
              onTap: () {
                player.playQueue(_songResults,
                    startIndex: _songResults.indexOf(song));
              },
              onMoreTap: () => SongOptionsSheet.show(context, song),
            );
          }),
        ],
      ]),
    );
  }
}
